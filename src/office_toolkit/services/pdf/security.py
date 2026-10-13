"""PDF password protection and authorized decryption (Phase 4, Fitur H-I).

Protection uses verified AES encryption via PyMuPDF. Passwords are never logged,
stored in configuration, written to history, or included in messages. Password
protection is not absolute security; permission flags are advisory hints whose
enforcement varies between viewers. Decryption is allowed only with a known
password and never attempts to crack or bypass protection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import pymupdf

from office_toolkit.core.errors import OutputError, ValidationError
from office_toolkit.services.pdf.common import (
    open_pdf,
    safe_output_path,
    write_verified_pdf,
)

ALGORITHMS = {
    "AES-256": pymupdf.PDF_ENCRYPT_AES_256,
    "AES-128": pymupdf.PDF_ENCRYPT_AES_128,
}


@dataclass
class EncryptResult:
    input: Path
    output: Path
    page_count: int
    algorithm: str
    output_size: int
    is_encrypted: bool
    warnings: List[str] = field(default_factory=list)


@dataclass
class DecryptResult:
    input: Path
    output: Path
    page_count: int
    was_encrypted: bool
    is_encrypted: bool


def _validate_passwords(user_pw: str, owner_pw: str) -> None:
    if not user_pw or not owner_pw:
        raise ValidationError("Kata sandi pengguna dan pemilik tidak boleh kosong.")
    if len(user_pw) < 4:
        raise ValidationError("Kata sandi pengguna minimal 4 karakter.")
    if len(owner_pw) < 4:
        raise ValidationError("Kata sandi pemilik minimal 4 karakter.")


def _open_probe(path: Path) -> bool:
    """Return True if ``path`` is password-protected, without authenticating."""
    try:
        probe = pymupdf.open(stream=path.read_bytes(), filetype="pdf")
    except Exception:
        return False
    try:
        return bool(getattr(probe, "needs_pass", False) or probe.is_encrypted)
    finally:
        probe.close()


def _permission_flags(
    allow_print: bool,
    allow_copy: bool,
    allow_modify: bool,
    allow_annotate: bool,
) -> int:
    flags = 0
    if allow_print:
        flags |= pymupdf.PDF_PERM_PRINT | pymupdf.PDF_PERM_PRINT_HQ
    if allow_copy:
        flags |= pymupdf.PDF_PERM_COPY | pymupdf.PDF_PERM_ACCESSIBILITY
    if allow_modify:
        flags |= pymupdf.PDF_PERM_MODIFY | pymupdf.PDF_PERM_FORM | pymupdf.PDF_PERM_ASSEMBLE
    if allow_annotate:
        flags |= pymupdf.PDF_PERM_ANNOTATE
    return flags


def encrypt_pdf(
    input_path: str | Path,
    user_pw: str,
    owner_pw: str,
    output_dir: str | Path,
    *,
    algorithm: str = "AES-256",
    allow_print: bool = True,
    allow_copy: bool = False,
    allow_modify: bool = False,
    allow_annotate: bool = False,
    output_name: Optional[str] = None,
) -> EncryptResult:
    """Protect a PDF with a user password (and a separate owner password)."""
    if algorithm not in ALGORITHMS:
        raise ValidationError(
            f"Algoritma enkripsi tidak didukung: {algorithm} (pilihan: {', '.join(ALGORITHMS)})"
        )
    _validate_passwords(user_pw, owner_pw)

    src = Path(input_path)
    doc = open_pdf(src)
    warnings: List[str] = [
        "Proteksi kata sandi bukan jaminan absolut terhadap semua metode serangan. "
        "Izin dokumen bersifat himbauan: penegakannya berbeda-beda antar viewer dan "
        "tidak sama dengan kontrol akses server."
    ]
    try:
        count = doc.page_count
        out_path = safe_output_path(
            Path(output_dir),
            (output_name or f"{src.stem}_terproteksi.pdf"),
            allow_overwrite=False,
        )
        flags = _permission_flags(allow_print, allow_copy, allow_modify, allow_annotate)
        write_verified_pdf(
            doc,
            out_path,
            count,
            encryption=ALGORITHMS[algorithm],
            user_pw=user_pw,
            owner_pw=owner_pw,
            permissions=flags,
            garbage=4,
            deflate=True,
            preserve_metadata=True,
            open_password=user_pw,
            expect_encrypted=True,
        )
    finally:
        doc.close()

    return EncryptResult(
        input=src,
        output=out_path,
        page_count=count,
        algorithm=algorithm,
        output_size=out_path.stat().st_size,
        is_encrypted=True,
        warnings=warnings,
    )


def decrypt_pdf(
    input_path: str | Path,
    user_pw: str,
    output_dir: str | Path,
    *,
    output_name: Optional[str] = None,
) -> DecryptResult:
    """Create an unencrypted copy using a known password (authorized use only)."""
    if not user_pw:
        raise ValidationError("Kata sandi tidak boleh kosong.")

    src = Path(input_path)
    # Probe encryption state on a fresh open. IMPORTANT (PyMuPDF 1.28.x quirk):
    # reading ``doc.needs_pass`` *after* a successful authenticate() flips the
    # document into a state where content streams are no longer decryptable. We
    # therefore determine password-protection from a separate, unauthenticated
    # probe and never touch those attributes on the authenticated document.
    probe = _open_probe(src)
    if not probe:
        raise ValidationError(
            "PDF ini tidak dilindungi kata sandi; tidak perlu dibuka proteksinya."
        )
    doc = open_pdf(src, password=user_pw)
    try:
        count = doc.page_count
        out_path = safe_output_path(
            Path(output_dir),
            (output_name or f"{src.stem}_tanpa_proteksi.pdf"),
            allow_overwrite=False,
        )
        # Rebuild page content into a fresh unencrypted document. Saving a
        # password-authenticated document directly with PDF_ENCRYPT_NONE can keep
        # broken (still-encrypted) content streams in PyMuPDF 1.28.x; a rebuild
        # guarantees readable, unencrypted output. Bookmarks/metadata are not
        # guaranteed to survive (same documented limitation as merge/split).
        new = pymupdf.open()
        try:
            for n in range(count):
                new.insert_pdf(doc, from_page=n, to_page=n)
            write_verified_pdf(
                new,
                out_path,
                count,
                garbage=3,
                deflate=True,
                preserve_metadata=True,
                expect_encrypted=False,
            )
        finally:
            new.close()
    finally:
        doc.close()

    return DecryptResult(
        input=src,
        output=out_path,
        page_count=count,
        was_encrypted=True,
        is_encrypted=False,
    )
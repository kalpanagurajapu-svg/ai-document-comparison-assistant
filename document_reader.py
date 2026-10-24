
from pypdf import PdfReader
from io import BytesIO


def extract_pdf_text(uploaded_file):
    """Extract readable text from an uploaded PDF."""

    try:
        pdf_bytes = uploaded_file.getvalue()
        reader = PdfReader(BytesIO(pdf_bytes))

        if len(reader.pages) == 0:
            raise ValueError("This PDF contains no pages.")

        pages_text = []
        unreadable_pages = []

        for page_number, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""

            if text.strip():
                pages_text.append(
                    f"[Page {page_number}]\n{text.strip()}"
                )
            else:
                unreadable_pages.append(page_number)

        full_text = "\n\n".join(pages_text)

        if not full_text.strip():
            raise ValueError(
                "No readable text found. "
                "This may be a scanned PDF."
            )

        return {
            "text": full_text,
            "page_count": len(reader.pages),
            "character_count": len(full_text),
            "unreadable_pages": unreadable_pages,
        }

    except ValueError:
        raise
    except Exception as error:
        raise ValueError(
            "Unable to read this PDF. Please upload a valid PDF."
        ) from error

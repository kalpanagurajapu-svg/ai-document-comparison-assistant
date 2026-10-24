
import streamlit as st

from document_reader import extract_pdf_text
from comparison import compare_documents
from report_generator import generate_comparison_report


st.set_page_config(
    page_title="AI Document Comparison Assistant",
    page_icon="📄",
    layout="wide",
)

st.title("📄 AI Document Comparison Assistant")

st.write(
    "Upload two text-based PDF documents to summarize their content, "
    "identify similarities and differences, compare key details, "
    "and download a comparison report."
)

st.info(
    "This tool provides informational comparisons only. "
    "Always verify important findings against the original documents."
)


# Keep the results available while the user views the sections.
if "comparison_result" not in st.session_state:
    st.session_state.comparison_result = None

if "file_names" not in st.session_state:
    st.session_state.file_names = None


col_a, col_b = st.columns(2)

with col_a:
    file_a = st.file_uploader(
        "Upload Document A (PDF)",
        type=["pdf"],
        key="document_a",
    )

with col_b:
    file_b = st.file_uploader(
        "Upload Document B (PDF)",
        type=["pdf"],
        key="document_b",
    )


if file_a:
    st.caption(f"Document A: {file_a.name}")

if file_b:
    st.caption(f"Document B: {file_b.name}")
data_a = None
data_b = None     
if file_a and file_b:
    if file_a.size == 0 or file_b.size == 0:
        st.error("One of the uploaded files is empty.")
    else:
        try:
            data_a = extract_pdf_text(file_a)
            data_b = extract_pdf_text(file_b)

            with st.expander("Preview extracted PDF text"):
                preview_a, preview_b = st.columns(2)

                with preview_a:
                    st.subheader("Document A")
                    st.write(f"Pages: {data_a['page_count']}")
                    st.write(
                        f"Characters: {data_a['character_count']}"
                    )
                    st.text(data_a["text"][:1500])

                with preview_b:
                    st.subheader("Document B")
                    st.write(f"Pages: {data_b['page_count']}")
                    st.write(
                        f"Characters: {data_b['character_count']}"
                    )
                    st.text(data_b["text"][:1500])

            unreadable = (
                data_a["unreadable_pages"]
                + data_b["unreadable_pages"]
            )

            if unreadable:
                st.warning(
                    "Some pages have no extractable text. "
                    "They may contain images or scanned content."
                )

        except ValueError as error:
            st.error(str(error))
            data_a = None
            data_b = None
else:
    data_a = None
    data_b = None
    st.info("Please upload both PDF documents to continue.")


if st.button(
    "Compare Documents",
    type="primary",
    disabled=not (file_a and file_b and data_a and data_b),
):
    try:
        with st.spinner(
            "Summarizing and comparing both documents..."
        ):
            result = compare_documents(
                data_a["text"],
                data_b["text"],
            )

        st.session_state.comparison_result = result
        st.session_state.file_names = (file_a.name, file_b.name)
        st.success("Comparison completed successfully!")

    except Exception as error:
        st.error(str(error))


result = st.session_state.comparison_result

if result:
    names = st.session_state.file_names

    st.divider()
    st.header("Comparison Results")

    tab_a, tab_b, tab_sim, tab_diff, tab_details, tab_conclusion = (
        st.tabs(
            [
                "Summary A",
                "Summary B",
                "Similarities",
                "Differences",
                "Key Details",
                "Conclusion",
            ]
        )
    )

    with tab_a:
        st.subheader(names[0])
        st.write(result["summary_a"])

    with tab_b:
        st.subheader(names[1])
        st.write(result["summary_b"])

    with tab_sim:
        st.subheader("Similarities")
        if result["similarities"]:
            for item in result["similarities"]:
                st.markdown(f"- {item}")
        else:
            st.write("No similarities identified.")

    with tab_diff:
        st.subheader("Differences")
        if result["differences"]:
            for item in result["differences"]:
                with st.expander(
                    str(item.get("topic", "Difference"))
                ):
                    st.write(
                        f"**Change type:** "
                        f"{item.get('change_type', 'Not specified')}"
                    )
                    st.write(
                        f"**Document A:** {item.get('document_a', 'Not found in the provided text')}"
                    )
                    st.write(
                        f"**Document B:** {item.get('document_b', 'Not found in the provided text')}"
                    )
                    st.write(
                        f"**Evidence A:** {item.get('evidence_a', 'Not provided')}"
                    )
                    st.write(
                        f"**Evidence B:** {item.get('evidence_b', 'Not provided')}"
                    )
        else:
            st.write("No meaningful differences identified.")

    with tab_details:
        st.subheader("Key Details Comparison")
        if result["key_details"]:
            st.dataframe(
                [
                    {
                        "Detail": item.get("detail", ""),
                        "Document A": item.get("document_a", ""),
                        "Document B": item.get("document_b", ""),
                    }
                    for item in result["key_details"]
                ],
                use_container_width=True,
            )
        else:
            st.write("No key details returned.")

    with tab_conclusion:
        st.subheader("Overall Conclusion")
        st.write(result["conclusion"])

        st.subheader("Limitations")
        limitations = result.get("limitations", [])
        if limitations:
            for item in limitations:
                st.markdown(f"- {item}")
        else:
            st.write(
                "AI output may contain errors. Verify important "
                "details against the original PDFs."
            )

    report = generate_comparison_report(
        result,
        names[0],
        names[1],
    )

    st.download_button(
        "Download Comparison Report (.docx)",
        data=report,
        file_name="document_comparison_report.docx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
    )

    if st.button("Reset and Compare Again"):
        st.session_state.comparison_result = None
        st.session_state.file_names = None
        st.rerun()

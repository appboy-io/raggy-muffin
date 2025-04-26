import streamlit as st
from rag import retrieve_relevant_chunks, generate_answer

def query_page():
    st.title("🔎 Ask a Question")

    tenant_id = st.text_input("Tenant ID", "default_tenant")
    question = st.text_input("Enter your question:")

    if st.button("Ask"):
        st.info("Retrieving context...")
        context_chunks = retrieve_relevant_chunks(question, tenant_id)

        if not context_chunks:
            st.warning("No relevant context found.")
            return

        st.info("Generating answer...")
        answer = generate_answer(question, context_chunks)
        st.success(answer)

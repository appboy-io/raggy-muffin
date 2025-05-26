import streamlit as st
from rag import retrieve_relevant_chunks, generate_answer
import traceback

def query_page():
    st.title("🔎 Ask a Question")

    tenant_id = st.text_input("Tenant ID", "default_tenant")
    question = st.text_input("Enter your question:")
    
    # Add debug mode toggle
    debug_mode = st.sidebar.checkbox("Debug Mode", value=False)

    if st.button("Ask"):
        try:
            if not question:
                st.warning("Please enter a question.")
                return
                
            with st.spinner("Retrieving context..."):
                context_chunks = retrieve_relevant_chunks(question, tenant_id)
                
                # If debug mode, show the context chunks
                if debug_mode:
                    st.write("Retrieved chunks:")
                    for i, chunk in enumerate(context_chunks):
                        st.text(f"Chunk {i+1}: {chunk[:100]}...")

            if not context_chunks:
                st.warning("No relevant context found in the database.")
                return

            with st.spinner("Generating answer..."):
                answer = generate_answer(question, context_chunks)
                
                # Display in a clean Q&A format
                st.markdown("### Question:")
                st.markdown(f"**{question}**")
                
                st.markdown("### Answer:")
                st.markdown(answer)
                
        except Exception as e:
            st.error("An error occurred")
            if debug_mode:
                st.code(traceback.format_exc())
            else:
                st.write("Try using a shorter, clearer question or check the database content.")

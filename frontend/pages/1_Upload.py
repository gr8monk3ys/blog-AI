import streamlit as st
import os

st.set_page_config(
    page_title="TAlker Upload",
    page_icon="🦙",
    layout="wide",
)

# @st.cache_resource
def initialize_files_list(directory='../data/'):
    """Initializes the files list in session state with files from the directory."""
    if 'files' not in st.session_state:
        st.session_state['files'] = list_files(directory)

@st.cache_data
def list_files(directory):
    """Lists files in the specified directory."""
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]


def add_file_to_directory(uploaded_file, directory='../data/'):
    """Saves the uploaded file to the specified directory."""
    file_path = os.path.join(directory, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

@st.cache_resource
def delete_file_from_directory(filename, directory='../data/'):
    """Deletes the specified file from the directory and updates the session state."""
    try:
        os.remove(os.path.join(directory, filename))
        return True
    except FileNotFoundError:
        return False

# @st.cache_resource
def display_uploaded_files(directory='../data/'):
    """Displays the list of uploaded files with an option to delete."""
    if 'files' in st.session_state:
        st.write("Uploaded Files:")
        to_delete = []
        for filename in st.session_state['files']:
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                st.write(filename)
            with col2:
                if st.button("X", key=filename):
                    # If deletion is successful, mark this filename for removal from session state
                    if delete_file_from_directory(filename, directory):
                        to_delete.append(filename)
                    else:
                        st.error(f"Failed to delete {filename}")
        # Update session state by removing deleted files
        for filename in to_delete:
            st.session_state['files'].remove(filename)

st.title("Upload")
initialize_files_list()
uploaded_file = st.file_uploader("Drag or Upload PDFs or Slides here", type=['pdf', 'png', 'jpg', 'jpeg', 'mp4', 'mp3'])
submit_button = st.button('Submit')
display_uploaded_files()
if submit_button:
    if uploaded_file is not None:
        # Save the uploaded file to the ../data/ directory and update the session state
        add_file_to_directory(uploaded_file)
        st.session_state['files'].append(uploaded_file.name)
        st.success("File submitted!")
    else:
        st.error("Please upload a file before submitting.")
# load_posts()
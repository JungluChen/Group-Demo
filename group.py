import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from PIL import Image
import io
from streamlit_star_rating import st_star_rating

# Initialize SQLite Database
conn = sqlite3.connect('comments.db', check_same_thread=False)
c = conn.cursor()

# Create tables if they don't exist
def create_tables():
    c.execute('''CREATE TABLE IF NOT EXISTS cv_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    school TEXT,
                    department TEXT,
                    picture BLOB,
                    capabilities TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS events_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cv_id INTEGER,
                    event_name TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    points TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cv_id INTEGER,
                    comment TEXT,
                    rating INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')
    conn.commit()

def add_cv(name, school, department, picture, capabilities):
    c.execute('INSERT INTO cv_data (name, school, department, picture, capabilities) VALUES (?, ?, ?, ?, ?)',
              (name, school, department, picture, capabilities))
    conn.commit()
    return c.lastrowid

def add_event(cv_id, event_name, start_date, end_date, points):
    c.execute('INSERT INTO events_data (cv_id, event_name, start_date, end_date, points) VALUES (?, ?, ?, ?, ?)',
              (cv_id, event_name, start_date, end_date, points))
    conn.commit()

def get_cvs():
    c.execute('SELECT * FROM cv_data')
    return c.fetchall()

def get_events(cv_id):
    c.execute('SELECT * FROM events_data WHERE cv_id=?', (cv_id,))
    return c.fetchall()

def get_comments(cv_id):
    c.execute('SELECT comment, rating, timestamp FROM comments WHERE cv_id=?', (cv_id,))
    return c.fetchall()

def add_comment(cv_id, comment, rating):
    c.execute('INSERT INTO comments (cv_id, comment, rating) VALUES (?, ?, ?)', (cv_id, comment, rating))
    conn.commit()

def get_average_rating(cv_id):
    c.execute('SELECT AVG(rating) FROM comments WHERE cv_id=?', (cv_id,))
    result = c.fetchone()[0]
    return result if result else 0

def display_stars(rating, max_rating=5):
    full_star = '★'
    empty_star = '☆'
    stars = full_star * int(rating) + empty_star * (max_rating - int(rating))
    return stars

def star_rating_input():
    st.markdown("### Your Rating")
    rating = st_star_rating("Please rate the CV by clicking on the stars below:", maxValue=5, defaultValue=0, key="rating_input")
    if rating == 0:
        st.warning("Please select a rating by clicking on the stars.")
    return rating

# Add event to CV
def add_event_to_cv():
    event_name = st.text_input('Event Name', key='event_name')
    start_date = st.date_input('Start Date', value=date.today(), key='start_date')
    end_date = st.date_input('End Date', value=date.today(), key='end_date')
    points = st.text_area('Responsibilities or Achievements (use bullet points)', key='points')

    if st.button('Add Event'):
        if event_name and points:
            new_event = {
                'name': event_name,
                'start': start_date,
                'end': end_date,
                'points': points.split("\n")
            }
            st.session_state['events'].append(new_event)
            st.success('Event added!')
        else:
            st.error('Please fill in the event name and points')

# Display events
def display_events(events):
    for event in events:
        st.write(f"### {event['name']} ({event['start']} - {event['end']})")
        for point in event['points']:
            st.write(f"- {point}")

# Create CV page
def create_cv_page():
    st.header('Create Your CV')
    # st.markdown("---").
    st.markdown("<hr style='border: 1px solid #D3D3D3;'>", unsafe_allow_html=True)
    name = st.text_input('Name')
    school = st.text_input('School')
    department = st.text_input('Department')
    picture_file = st.file_uploader('Upload Picture', type=['jpg', 'jpeg', 'png'])
    st.markdown("<hr style='border: 1px solid #D3D3D3;'>", unsafe_allow_html=True)
    # Capabilities Input
    st.subheader("Add Your Capabilities")
    capabilities = st.text_area("Enter your capabilities, separated by commas (e.g., Python, Data Analysis, Leadership)")
    st.markdown("<hr style='border: 1px solid #D3D3D3;'>", unsafe_allow_html=True)

    st.subheader("Add Your Experiences/Events")

    # Initialize session state for events
    if 'events' not in st.session_state:
        st.session_state['events'] = []

    add_event_to_cv()
    st.markdown("<hr style='border: 1px solid #D3D3D3;'>", unsafe_allow_html=True)
    # Preview events
    st.subheader("Events Preview")
    if st.session_state['events']:
        display_events(st.session_state['events'])
    else:
        st.info("No events added yet.")

    if st.button('Submit CV'):
        if name and school and department and picture_file and st.session_state['events'] and capabilities:
            picture = picture_file.read()
            cv_id = add_cv(name, school, department, picture, capabilities)
            for event in st.session_state['events']:
                add_event(cv_id, event['name'], event['start'], event['end'], "\n".join(event['points']))
            st.success('Your CV has been submitted!')
            st.session_state['events'] = []  # Clear events after submission
        else:
            st.error('Please fill in all fields, add at least one event, and add capabilities')

# View CVs page
def view_cvs_page():
    st.header('View Submitted CVs')

    cvs = get_cvs()
    if cvs:
        cv_dict = {cv[1]: cv for cv in cvs}
        cv_names = list(cv_dict.keys())

        selected_cv_name = st.selectbox('Select a CV to view:', cv_names)
        st.markdown("<hr style='border: 1px solid #D3D3D3;'>", unsafe_allow_html=True)    
        if selected_cv_name:
            selected_cv = cv_dict[selected_cv_name]
            st.subheader(selected_cv[1])  # Name

            # Display Picture
            if selected_cv[4]:
                image = Image.open(io.BytesIO(selected_cv[4]))
                st.image(image, caption=selected_cv[1], use_column_width=True)

            st.write(f'**School:** {selected_cv[2]}')
            st.write(f'**Department:** {selected_cv[3]}')
            st.markdown("<hr style='border: 1px solid #D3D3D3;'>", unsafe_allow_html=True)           
            # Display Capabilities
            st.subheader("Capabilities")

            capabilities_list = selected_cv[5].split(',')
            for capability in capabilities_list:
                st.write(f"- {capability.strip()}")
            st.markdown("<hr style='border: 1px solid #D3D3D3;'>", unsafe_allow_html=True)
            st.subheader("Experiences/Events")

            events = get_events(selected_cv[0])
            for event in events:
                st.write(f"### {event[2]} ({event[3]} - {event[4]})")
                for point in event[5].split("\n"):
                    st.write(f"- {point}")

            # Display Average Rating
            average_rating = get_average_rating(selected_cv[0])
            stars = display_stars(round(average_rating))
            st.markdown("<hr style='border: 1px solid #D3D3D3;'>", unsafe_allow_html=True)
            st.write(f'**Average Rating:** {stars} ({average_rating:.1f}/5)')

            st.subheader('Comments')
            comments = get_comments(selected_cv[0])
            for comment, rating, timestamp in comments:
                stars = display_stars(rating)
                st.write(f'*{timestamp}* - **Rating:** {stars} ({rating}/5) - {comment}')

            st.subheader('Add a Comment and Rating')
            comment_text = st.text_area('Your Comment', key='comment')
            rating = star_rating_input()
            if st.button('Submit Comment'):
                if comment_text and rating > 0:
                    add_comment(selected_cv[0], comment_text, rating)
                    st.success('Comment and rating added!')
                    st.experimental_rerun()
                else:
                    st.error('Please enter a comment and select a rating.')
    else:
        st.info('No CVs available. Please create one!')

# Main function
def main():
    st.title('CV Showcase and Comments')
    create_tables()

    menu = ['Create CV', 'View CVs']
    choice = st.sidebar.selectbox('Menu', menu)

    if choice == 'Create CV':
        create_cv_page()
    elif choice == 'View CVs':
        view_cvs_page()

if __name__ == '__main__':
    main()

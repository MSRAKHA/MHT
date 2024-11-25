import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import bcrypt
import sqlite3
import os
import time
import os
import random
import google.generativeai as genai 
import base64
from pygame import mixer # type: ignore
st.set_page_config(page_title="MoodLens", page_icon="§ ", layout="wide")
# At the start of your app, after imports
def init_session_state():
    if 'authentication_status' not in st.session_state:
        st.session_state['authentication_status'] = {
            'logged_in': False
        }

# Call the initialization function
init_session_state()



if st.session_state['authentication_status']['logged_in']:
    username = st.session_state['authentication_status']['username']
    
    # Add username to sidebar
    with st.sidebar:
        st.markdown(f"""
            <div style='
                padding: 8px; 
                text-color: #f0f2f6;
                text-align: center; 
                font-weight: bold;
                border-bottom: 2px solid #f0f2f6;
                margin-bottom: 10px;'>
                ‘¤ Welcome {username}!
            </div>
        """, unsafe_allow_html=True)

      

# Add this near the top of your app, after imports
def init_session_state():
    if 'authentication_status' not in st.session_state:
        st.session_state['authentication_status'] = {
            'logged_in': False,
            'username': None}
# Call this function before your main() function
init_session_state()
# Database initialization
DATABASE_PATH = "./databases/mental_health.db"
# Create database directory if it doesn't exist
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password BLOB NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
    ''')   # First, check if the table exists
    c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='mental_health_data' ''')   
    if c.fetchone()[0] == 0:
       # Table doesn't exist, create it with all columns
        c.execute('''
            CREATE TABLE mental_health_data (
                username TEXT NOT NULL,
                data_type TEXT NOT NULL,
                activity_type TEXT,
                activity_duration INTEGER,
                intensity TEXT,
                mood TEXT,
                anxiety INTEGER,
                stress INTEGER,
                sleep_hours REAL,
                sleep_quality TEXT,
                journal_entry TEXT,
                goal_description TEXT,
                goal_status TEXT,
                duration INTEGER,
                date INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users (username)
            )
        ''')
    else:
        # Table exists, safely add new columns if they don't exist
        columns_to_add = [
            ('activity_type', 'TEXT'),
            ('activity_duration', 'INTEGER'),
            ('goal_description', 'TEXT'),
            ('goal_status', 'TEXT'),
            ('duration', 'INTEGER'),
            ('date', 'INTEGER')]
        for column_name, column_type in columns_to_add:
            try:
                c.execute(f'ALTER TABLE mental_health_data ADD COLUMN {column_name} {column_type}')
                conn.commit()
            except sqlite3.OperationalError:
                # Column already exists, continue to next column
                continue
    conn.commit()
    conn.close()
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)
def register_user(username, password, email):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    try:
        hashed_password = hash_password(password)
        c.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                 (username, hashed_password, email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
def login_user(username, password):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    
    if result and verify_password(password, result[0]):
        # Set the session state when login is successful
        st.session_state['authentication_status'] = {
            'logged_in': True,
            'username': username
        }
        return True

    return False
# Function to save meditation data
def save_meditation_data(username, duration):
    conn = sqlite3.connect(DATABASE_PATH)
    
    c = conn.cursor()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        c.execute('''
            INSERT INTO mental_health_data 
            (username, data_type, duration, timestamp) 
            VALUES (?, ?, ?)
        ''', (username, 'meditation', duration , current_time))
        conn.commit()
        st.success(f"Successfully saved your meditation session of {duration} minutes!")
        st.success("Meditation data saved successfully!")

    except sqlite3.Error as e:
        st.error(f"Error saving data: {str(e)}")
    finally:
        conn.close()
# Function to save goal data
def save_goal_data(username, goal_description):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO mental_health_data 
            (username, data_type, goal_description) 
            VALUES (?, ?, ?)
        ''', (username, 'goal', goal_description))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error saving data: {str(e)}")
    finally:
        conn.close()
def save_mental_health_data(data_type, data):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()    
    # Prepare the base data
    base_data = {
        'username': st.session_state.authentication_status['username'],
        'data_type': data_type,
        'timestamp': datetime.now()
    }    
    # Combine base_data with the specific data
    full_data = {**base_data, **data}    
    # Create the SQL query dynamically based on the data
    columns = ', '.join(full_data.keys())
    placeholders = ', '.join(['?' for _ in full_data])
    query = f'INSERT INTO mental_health_data ({columns}) VALUES ({placeholders})'   
    try:
        c.execute(query, list(full_data.values()))      
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False
    finally:
        conn.close()
def save_checkin_data(username, data_type, **data):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()    
    # Add current timestamp
    data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['username'] = username
    data['data_type'] = data_type   
    # Create columns and values for SQL query
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data])
    values = tuple(data.values())    
    query = f'INSERT INTO mental_health_data ({columns}) VALUES ({placeholders})'    
    try:
        c.execute(query, values)
        conn.commit()
        st.success(f"Successfully saved your {data_type} check-in!")
    except sqlite3.Error as e:
        st.error(f"Error saving data: {e}")
    finally:
        conn.close()
def get_user_checkins(username):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()   
    query = '''
        SELECT data_type, mood, anxiety, stress, sleep_hours, sleep_quality,
               journal_entry, duration, goal_description, goal_status, timestamp
        FROM mental_health_data
        WHERE username = ?
        ORDER BY timestamp DESC
    '''   
    c.execute(query, (username,))
    results = c.fetchall()
    columns = ['data_type', 'mood', 'anxiety', 'stress', 'sleep_hours', 'sleep_quality',
              'journal_entry', 'duration', 'goal_description', 'goal_status', 'timestamp']   
    df = pd.DataFrame(results, columns=columns)
    conn.close()
    return df
def display_checkins():
    st.title(" *:rainbow[Your Check-in History]*")
    
    if not st.session_state.authentication_status['logged_in']:
        st.sidebar.title(f"Welcome, {st.session_state.authentication_status['username']}")

        st.warning("Please login to view your check-in history")
        return 
    username = st.session_state.authentication_status['username']
    df = get_user_checkins(username)
    if df.empty:
        st.info("No check-ins found. Start tracking your mental health journey!")
        return
    if not df.empty:
        st.dataframe(df)
         # Add a button to get insights
        if st.button("Get AI Insights"):
            with st.spinner("Analyzing your mental health data..."):
                insights = get_chatbot_insights(username)
                
                # Display insights in a nice format
                st.markdown("### ¤– AI Insights & Recommendations")
                st.markdown(insights)
                
                # Add a disclaimer
                st.info("""
                    Note: These insights are generated by AI and should not replace professional medical advice. 
                    If you're experiencing serious mental health concerns, please consult a healthcare professional.
                    """)
    else:
        st.info("No check-in data available yet. Start by adding some check-ins!") 
    # Fetch all data
    conn = sqlite3.connect(DATABASE_PATH)
    df = pd.read_sql_query('''
        SELECT * FROM mental_health_data 
        WHERE username = ? 
        ORDER BY timestamp DESC
    ''', conn, params=(username,))
    conn.close()   
    if df.empty:
        st.info("No check-ins found. Start tracking your mental health journey!")
        return
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])  
    # Create tabs for different views
    tab1, tab2 , tab3 ,tab4 , tab5 ,tab6 ,tab7 = st.tabs([" Mood Check"," Sleep Data" ,"Activity Tracking", " Journal Thoughts Data" ,"  Meditation " , "  Goals" ,"Raw Data"])
    with tab1:
        mental_health_df = df[df['data_type'] == 'mental_health'].copy()
        if not mental_health_df.empty:
            mental_health_df = mental_health_df.sort_values('timestamp')
            # 1. Mood Analysis
            st.subheader("˜Š *:blue[Mood Analysis]*")
            col1, col2 = st.columns(2)           
            with col1:
                # Mood Distribution Pie Chart
                mood_counts = mental_health_df['mood'].value_counts()
                fig_mood_pie = px.pie(
                    values=mood_counts.values,
                    names=mood_counts.index,
                    title='Overall Mood Distribution',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig_mood_pie, use_container_width=True)           
            with col2:
                # Mood Trend Line
                fig_mood_trend = px.line(
                    mental_health_df,
                    x='timestamp',
                    y='mood',
                    title='Mood Trends Over Time',
                    color_discrete_sequence=['#FF69B4']
                )
                fig_mood_trend.update_layout(yaxis_title='Mood Level')
                st.plotly_chart(fig_mood_trend, use_container_width=True)           
            # 2. Anxiety and Stress Analysis
            st.subheader("˜°  *:blue[Anxiety and Stress Patterns]*")           
            # Combined Anxiety and Stress Line Chart
            fig_metrics = go.Figure()           
            fig_metrics.add_trace(
                go.Scatter(
                    x=mental_health_df['timestamp'],
                    y=mental_health_df['anxiety'],
                    name='Anxiety',
                    line=dict(color='#FF9999', width=2),
                    mode='lines+markers'
                )
            )           
            fig_metrics.add_trace(
                go.Scatter(
                    x=mental_health_df['timestamp'],
                    y=mental_health_df['stress'],
                    name='Stress',
                    line=dict(color='#66B2FF', width=2),
                    mode='lines+markers'))           
            fig_metrics.update_layout(
                title='Anxiety and Stress Levels Over Time',
                xaxis_title='Date',
                yaxis_title='Level (0-10)',
                hovermode='x unified',
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01))            
            st.plotly_chart(fig_metrics, use_container_width=True)
            # Separate Analysis for Anxiety and Stress
            col1, col2 = st.columns(2)
            with col1:
                # Anxiety Distribution
                fig_anxiety = px.histogram(
                    mental_health_df,
                    x='anxiety',
                    title='Anxiety Level Distribution',
                    color_discrete_sequence=['#FF9999'],
                    nbins=10
                )
                fig_anxiety.update_layout(
                    xaxis_title='Anxiety Level',
                    yaxis_title='Frequency'
                )
                st.plotly_chart(fig_anxiety, use_container_width=True)            
            with col2:
                # Stress Distribution
                fig_stress = px.histogram(
                    mental_health_df,
                    x='stress',
                    title='Stress Level Distribution',
                    color_discrete_sequence=['#66B2FF'],
                    nbins=10
                )
                fig_stress.update_layout(
                    xaxis_title='Stress Level',
                    yaxis_title='Frequency'
                )
                st.plotly_chart(fig_stress, use_container_width=True)
            # 3. Journal Entry Analysis
            st.subheader("“  *:blue[Journal Entries Mood]* ")            
            # Recent journal entries with mood context
            recent_entries = mental_health_df[['timestamp', 'mood', 'anxiety', 'stress', 'journal_entry']].head(5)
            for _, entry in recent_entries.iterrows():
                if pd.notna(entry['journal_entry']):
                    with st.expander(f"Entry from {entry['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Mood", entry['mood'])
                        with col2:
                            st.metric("Anxiety", f"{entry['anxiety']}/10")
                        with col3:
                            st.metric("Stress", f"{entry['stress']}/10")
                        st.write("Journal Entry:", entry['journal_entry'])            
            # 4. Summary Statistics
            st.subheader("  *:blue[Summary Statistics]*")
            col1, col2, col3 = st.columns(3)            
            with col1:
                avg_anxiety = mental_health_df['anxiety'].mean()
                st.metric(
                    "Average Anxiety",
                    f"{avg_anxiety:.1f}/10",
                    delta=f"{avg_anxiety - mental_health_df['anxiety'].iloc[-1]:.1f}"
                )            
            with col2:
                avg_stress = mental_health_df['stress'].mean()
                st.metric(
                    "Average Stress",
                    f"{avg_stress:.1f}/10",
                    delta=f"{avg_stress - mental_health_df['stress'].iloc[-1]:.1f}"
                )
            
            with col3:
                most_common_mood = mental_health_df['mood'].mode()[0]
                st.metric("Most Common Mood", most_common_mood)            
            # 5. Weekly Trends
            st.subheader("“…  *:blue[Weekly Trends]*")
            mental_health_df['week'] = mental_health_df['timestamp'].dt.strftime('%Y-%U')
            weekly_stats = mental_health_df.groupby('week').agg({
                'anxiety': 'mean',
                'stress': 'mean'
            }).reset_index()
            
            fig_weekly = go.Figure()
            
            fig_weekly.add_trace(
                go.Scatter(
                    x=weekly_stats['week'],
                    y=weekly_stats['anxiety'],
                    name='Weekly Anxiety',
                    line=dict(color='#FF9999', width=2)
                )
            )
            fig_weekly.add_trace(
                go.Scatter(
                    x=weekly_stats['week'],
                    y=weekly_stats['stress'],
                    name='Weekly Stress',
                    line=dict(color='#66B2FF', width=2)
                )
            )            
            fig_weekly.update_layout(
                title='Weekly Average Trends',
                xaxis_title='Week',
                yaxis_title='Average Level',
                hovermode='x unified'
            )
            st.plotly_chart(fig_weekly, use_container_width=True)           
        else:
            st.info("No mental health check-ins recorded yet.")
    with tab2:
        st.subheader(" *:blue[Œ› Sleep Patterns]*")
        sleep_df = df[df['data_type'] == 'sleep'].copy()
        if not sleep_df.empty:
            #st.subheader(" *:blue[Sleep Patterns]*")
                       # Prepare data for visualization
            sleep_df = sleep_df.sort_values('timestamp')
            
            # Sleep Duration Line Chart
            fig_sleep = go.Figure()
            fig_sleep.add_trace(
                go.Scatter(
                    x=sleep_df['timestamp'],
                    y=sleep_df['sleep_hours'],
                    name='Sleep Duration',
                    line=dict(color='#9966FF')
                )
            )            
            fig_sleep.update_layout(
                title='Sleep Duration Over Time',
                xaxis_title='Date',
                yaxis_title='Hours',
                hovermode='x unified'
            )
            st.plotly_chart(fig_sleep, use_container_width=True)            
            # Sleep Quality Distribution
            col1, col2 = st.columns(2)
            with col1:
                quality_counts = sleep_df['sleep_quality'].value_counts()
                fig_quality = px.pie(
                    values=quality_counts.values,
                    names=quality_counts.index,
                    title='Sleep Quality Distribution',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig_quality, use_container_width=True)            
            # Recent entries
            with col2:
                st.subheader(" *:blue[Recent Sleep Notes]*")
                recent_sleep = sleep_df[['timestamp', 'sleep_hours', 'sleep_quality', 'journal_entry']].head(3)
                for _, row in recent_sleep.iterrows():
                    with st.expander(f"Entry from {row['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                        st.write(f"Sleep Duration: {row['sleep_hours']} hours")
                        st.write(f"Sleep Quality: {row['sleep_quality']}")
                        if pd.notna(row['journal_entry']):
                            st.write("Notes:", row['journal_entry'])
        else:
            st.info("No sleep tracking data recorded yet.")
    with tab3:
        st.subheader("*:blue[“” Activity Tracking]*")
        activity_df = df[df['data_type'] == 'activity'].copy()
        if not activity_df.empty:
            # Prepare data for visualization
            activity_df = activity_df.sort_values('timestamp')
            # Create activity duration trend
            fig_activity = px.line(
                activity_df,
                x='timestamp',
                y='activity_duration',
                title='Activity Duration Over Time',
                color_discrete_sequence=['#FFD700']
            )
            fig_activity.update_layout(
                xaxis_title='Date',
                yaxis_title='Duration (minutes)'
            )
            st.plotly_chart(fig_activity, use_container_width=True)
            # Show total activity statistics
            total_minutes = activity_df['activity_duration'].sum()
            total_sessions = len(activity_df)
            avg_duration = activity_df['activity_duration'].mean()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Activity Time", f"{total_minutes:.0f} mins")
            with col2:
                st.metric("Total Sessions", total_sessions)
            with col3:
                st.metric("Average Duration", f"{avg_duration:.1f} mins")
        else:
            st.info("No activity tracking data recorded yet.")            
    with tab4:      
        st.subheader("*:blue[“‘ Journal Thoughts Entries]*")            
            # Recent journal Thoughts 
        journal_df = df[df['data_type'] == 'journal'].copy()    
        if not journal_df.empty:
        # Sort by timestamp descending to show most recent entries first
            journal_df = journal_df.sort_values('timestamp', ascending=False)
        
        # Display journal entries with expandable sections
            for idx, entry in journal_df.iterrows():
                with st.expander(f"Journal Entry - {entry['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                    st.write(entry['journal_entry'])
                # Add mood context if available
                    if 'mood' in entry and pd.notna(entry['mood']):
                        st.write(f"Mood during entry: {entry['mood']}")
        else:
            st.info("No journal entries found. Start writing your thoughts!")         
    with tab5:        
        st.subheader(" *:blue[â±ï¸ Meditation Sessions]*")
        meditation_df = df[df['data_type'] == 'meditation'].copy()
        if not meditation_df.empty:
            # Prepare data for visualization
            meditation_df = meditation_df.sort_values('timestamp')
            # Create meditation duration trend
            fig_meditation = px.line(
            meditation_df,
            x='timestamp',
            y='duration',
            title='Meditation Duration Over Time',
            color_discrete_sequence=['#9370DB']
        )
            fig_meditation.update_layout(
            xaxis_title='Date',
            yaxis_title='Duration (minutes)',
            hovermode='x unified'
        )
            st.plotly_chart(fig_meditation, use_container_width=True)
                # Show total meditation statistics
            total_minutes = meditation_df['duration'].sum()
            total_sessions = len(meditation_df)
            avg_duration = meditation_df['duration'].mean()
        
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Meditation Time", f"{total_minutes:.0f} mins")
            with col2:
                st.metric("Total Sessions", total_sessions)
            with col3:
                st.metric("Average Duration", f"{avg_duration:.1f} mins")           
        else:
            st.info("No meditation sessions recorded yet. Start your meditation journey!")        
    with tab6:
        st.subheader("*:blue[Goals Progress]*")
        # Display goals
        goals_df = df[df['data_type'] == 'goal'].copy()    
        if not goals_df.empty:
            goals_df = goals_df.sort_values('timestamp', ascending=False)
               # Display goals in a more structured way
            for idx, goal in goals_df.iterrows():
                with st.expander(f"Goal set on {goal['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                    st.write("*Goal Description:*")
                    st.write(goal['goal_description'])                
                    if 'goal_status' in goal and pd.notna(goal['goal_status']):
                        status_color = "¢" if goal['goal_status'].lower() == 'completed' else "¡"
                        st.write(f"*Status:* {status_color} {goal['goal_status']}")
                       # Add goal statistics if available
                        completed_goals = goals_df[goals_df['goal_status'].str.lower() == 'completed'].shape[0] if 'goal_status' in goals_df else 0
                        total_goals = len(goals_df)
        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Total Goals", total_goals)
                        with col2:
                            st.metric("Completed Goals", completed_goals)           
        # Optional: Add a pie chart for goal status distribution
                    if 'goal_status' in goals_df.columns:
                        status_counts = goals_df['goal_status'].value_counts()
                        fig_goals = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title='Goal Status Distribution',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
                        st.plotly_chart(fig_goals, use_container_width=True)
        else:
            st.info("No goals set yet. Start setting your mental health goals!")       
    with tab7:
        st.subheader(" *:blue[Complete History]*")
        current_time = datetime.now()
            # Format timestamp column
        df['formatted_timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        # Convert timestamp to datetime if it's not already
        df['timestamp'] = pd.to_datetime(df['formatted_timestamp'])
           # Format the timestamp
        df['Date'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
               # Rename columns for better display
        df = df.rename(columns={
        'data_type': 'Check-in Type',
        'mood': 'Mood',
        'anxiety': 'Anxiety Level',
        'stress': 'Stress Level',
        'sleep_hours': 'Sleep Hours',
        'sleep_quality': 'Sleep Quality',
        'activity_type': 'Activity Type',
        'activity_duration': 'Activity Duration (minutes)',
        'journal_entry': 'Journal Thoughts',
        'duration': 'Meditation (minutes)',
        'goal_description': 'Goal Description',
        'goal_status': 'Goal Status'
    })# Reorder columns
        columns_order = [
        'Date',
        'Check-in Type',
        'Mood',
        'Anxiety Level',
        'Stress Level',
        'Sleep Hours',
        'Sleep Quality',
        'Activity Type',
        'Activity Duration (minutes)',
        'Journal Thoughts',
        'Meditation (minutes)',
        'Goal Description',
        'Goal Status']
       # Select and reorder columns
        df_display = df[columns_order]   
    # Replace NaN values with empty string for better display
        df_display = df_display.fillna('')
    # Display the complete history table
        #st.subheader("Complete History")
        st.dataframe(
        df_display,
        use_container_width=True,
        
        hide_index=True
    )
def generate_insights(df):
    insights = {}
    try:
        # Mood Analysis
        if 'mood' in df.columns and not df['mood'].empty:
            mood_counts = df['mood'].value_counts()
            most_common_mood = mood_counts.index[0] if not mood_counts.empty else "No data"
            insights['mood'] = {
                'most_common': most_common_mood,
                'distribution': mood_counts.to_dict()
            }
        
        # Sleep Analysis
        if 'sleep_hours' in df.columns and not df['sleep_hours'].empty:
            avg_sleep = df['sleep_hours'].mean()
            sleep_quality_dist = df['sleep_quality'].value_counts() if 'sleep_quality' in df.columns else None
            insights['sleep'] = {
                'average_hours': round(avg_sleep, 2),
                'quality_distribution': sleep_quality_dist.to_dict() if sleep_quality_dist is not None else {}
            }
        
        # Stress and Anxiety Analysis
        if 'stress' in df.columns and 'anxiety' in df.columns:
            avg_stress = df['stress'].mean()
            avg_anxiety = df['anxiety'].mean()
            insights['mental_state'] = {
                'average_stress': round(avg_stress, 2),
                'average_anxiety': round(avg_anxiety, 2)
            }
        
        return insights
    except Exception as e:
        st.error(f"An error occurred: {e}")
    return {}
   

def generate_guidance(insights):
    guidance = []
    try:
    # Mood-based guidance
        if 'mood' in insights:
            most_common_mood = insights['mood']['most_common']
            if most_common_mood in ['sad', 'angry', 'anxious']:
                guidance.append({
                    'category': 'Mood',
                    'suggestion': "Consider practicing mindfulness or meditation to improve your mood.",
                    'action_items': [
                        "Try a 10-minute meditation session",
                        "Write down three things you're grateful for",
                        "Take a short walk in nature"
                    ]
                })
        
        # Sleep-based guidance
        if 'sleep' in insights:
            avg_sleep = insights['sleep']['average_hours']
            if avg_sleep < 7:
                guidance.append({
                    'category': 'Sleep',
                    'suggestion': "You're getting less than the recommended 7-9 hours of sleep.",
                    'action_items': [
                        "Establish a regular sleep schedule",
                        "Avoid screens 1 hour before bedtime",
                        "Create a relaxing bedtime routine"
                    ]
                })
        
        # Stress and Anxiety guidance
        if 'mental_state' in insights:
            avg_stress = insights['mental_state']['average_stress']
            avg_anxiety = insights['mental_state']['average_anxiety']
            if avg_stress > 6 or avg_anxiety > 6:
                guidance.append({
                    'category': 'Stress Management',
                    'suggestion': "Your stress and anxiety levels are above average.",
                    'action_items': [
                        "Practice deep breathing exercises",
                        "Consider talking to a mental health professional",
                        "Incorporate regular exercise into your routine"
                    ]
                })
        
        return guidance
    except Exception as e:
        st.error(f"An error occurred: {e}")

def display_insights_page():
    st.title(" *:rainbow[Your Mental Health Insights]*")
    
    if not st.session_state.authentication_status['logged_in']:
        st.warning("Please login to view your insights")
        return
    
    username = st.session_state.authentication_status['username']
    df = get_user_checkins(username)
    
    if df.empty:
        st.info("No data available yet. Complete some check-ins to see your insights!")
        return
    
    insights = generate_insights(df)
    
    # Display Mood Insights
    if 'mood' in insights:
        st.subheader("˜Š Mood Analysis")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Most Common Mood", insights['mood']['most_common'])
        with col2:
            fig = px.pie(values=list(insights['mood']['distribution'].values()),
                        names=list(insights['mood']['distribution'].keys()),
                        title="Mood Distribution")
            st.plotly_chart(fig)
    
    # Display Sleep Insights
    if 'sleep' in insights:
        st.subheader("˜´ Sleep Analysis")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Average Sleep Duration", f"{insights['sleep']['average_hours']} hours")
        with col2:
            if insights['sleep']['quality_distribution']:
                fig = px.bar(x=list(insights['sleep']['quality_distribution'].keys()),
                           y=list(insights['sleep']['quality_distribution'].values()),
                           title="Sleep Quality Distribution")
                st.plotly_chart(fig)
    
    # Display Stress & Anxiety Insights
    if 'mental_state' in insights:
        st.subheader("§˜â€â™€ï¸ Stress & Anxiety Levels")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Average Stress Level", f"{insights['mental_state']['average_stress']}/10")
        with col2:
            st.metric("Average Anxiety Level", f"{insights['mental_state']['average_anxiety']}/10")

def display_guidance_page():
    st.title("Œ *:rainbow[Personalized Guidance]*")
    
    if not st.session_state.authentication_status['logged_in']:
        st.warning("Please login to view your personalized guidance")
        return
    
    username = st.session_state.authentication_status['username']
    df = get_user_checkins(username)
    
    if df.empty:
        st.info("Complete some check-ins to receive personalized guidance!")
        return
    
    insights = generate_insights(df)
    guidance = generate_guidance(insights)
    #display guidance 
    if not guidance:
        st.info("No personalized guidance available at the moment.")
        return
    for item in guidance:
        with st.expander(f"“Œ {item['category']} Guidance"):
            st.write(f"*Suggestion:* {item['suggestion']}")
            st.write("*Action Items:*")
            for action in item['action_items']:
                st.write(f"- {action}")
    

def game():
    st.title("Ž® *:rainbow[Simple Number Guessing Game]*")
    
    # Initialize game state
    if 'target_number' not in st.session_state:
        st.session_state.target_number = random.randint(1, 100)
    if 'attempts' not in st.session_state:
        st.session_state.attempts = 0

    # Game interface
    st.write("I'm thinking of a number between 1 and 100!")
    guess = st.number_input("Enter your guess:", min_value=1, max_value=100, step=1)
    
    if st.button("Make Guess"):
        st.session_state.attempts += 1
        
        if guess == st.session_state.target_number:
            st.success(f"Ž‰ Congratulations! You found the number in {st.session_state.attempts} attempts!")
            if st.button("Play Again"):
                st.session_state.target_number = random.randint(1, 100)
                st.session_state.attempts = 0
                st.rerun()
        elif guess < st.session_state.target_number:
            st.warning("Too low! Try a higher number.")
        else:
            st.warning("Too high! Try a lower number.")

    if st.button("Reset Game"):
        st.session_state.target_number = random.randint(1, 100)
        st.session_state.attempts = 0
        st.rerun()
def display_chatBot():
        os.environ['GOOGLE_API_KEY'] = "AIzaSyCBEOQfH0uTMjeJo1PEAUQ3ALxYxtMv3v8"
        genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
        st.title("ChatBot")
        model = genai.GenerativeModel("gemini-pro")
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "Ask me Anything."}
            ]
        for messages in st.session_state.messages:
            with st.chat_message(messages["role"]):
                st.markdown(messages["content"])
        def llm_function(query):
            response = model.generate_content(query)
            with st.chat_message("assistant"):
                st.markdown(response.text)
            st.session_state.messages.append({"role": "user", "content": query})
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        query = st.chat_input("Ask me Anything", key="user_input")
        if query:
          with st.chat_message("user"):
            st.markdown(query)
          llm_function(query)
        #clear chat history
        if st.button("Clear Chat History"):
            st.session_state.messages = [
                {"role": "assistant", "content": "Ask me Anything about Your Mental Health."}
            ]
            st.rerun()
 
 
       
def main():
    init_session_state()   
    # Sidebar for navigation
    if st.session_state.authentication_status['logged_in']:
        
        #st.sidebar.title(f"Welcome, {st.session_state.username}")

        page = st.sidebar.radio("*:rainbow[Menu]*", 
            ["Home", "Mental Health Check", "Sleep Tracking", 
             "Activity Tracking",
             "Journal Thoughts", "Meditation Timer", 
             "Goals","Check-in History" ,"Insights","Guidance","Game","ChatBot" ])        
        # Add logout button to sidebar
        if st.sidebar.button("*:rainbow[Logout]*"):
            logout()            
    else:
        page = st.sidebar.radio("*:rainbow[Navigation]*", ["Home", "Login", "Register"])   
   
    #page routing
    if not st.session_state.authentication_status['logged_in'] and page not in ["Home", "Login", "Register"]:
        st.warning("Please login to access this feature")
        page = "Login"

    if page == "Home":
        display_home()
    elif page == "Login":
        display_login()
    elif page == "Register":
        display_register()
    elif page == "Mental Health Check":
        mental_health_check()
    elif page == "Sleep Tracking":
        sleep_tracking()
    elif page == "Activity Tracking":
        activity_tracking()
   
    elif page == "Journal Thoughts":
        journal_Thoughts()
    elif page == "Meditation Timer":
        meditation_timer()
    elif page == "Goals":
        goals()
    elif page == "Check-in History":
        display_checkins()
    elif page == "Insights":
        display_insights_page()
    elif page == "Guidance":
        display_guidance_page()    
    elif page == "Game":
        game()
    elif page == "ChatBot":
        display_chatBot()

def add_bg_from_local(image_file):
    with open(image_file, "rb") as file:
        encoded_string = base64.b64encode(file.read()).decode()
    
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded_string}");
            background-size: cover;
            background-position:right;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Use the function
def get_chatbot_insights(username):
    # Connect to database and get user's recent data
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    query = '''
        SELECT data_type, mood, anxiety, stress, sleep_hours, sleep_quality,
               journal_entry, timestamp
        FROM mental_health_data
        WHERE username = ?
        ORDER BY timestamp DESC
        LIMIT 5
    '''
    
    c.execute(query, (username,))
    results = c.fetchall()
    conn.close()
    
    # Format the data into a meaningful prompt
    prompt = "Based on the following mental health data, provide supportive insights and guidance:\n\n"
    
    for entry in results:
        data_type, mood, anxiety, stress, sleep_hours, sleep_quality, journal, timestamp = entry
        prompt += f"Date: {timestamp}\n"
        if mood:
            prompt += f"Mood: {mood}\n"
        if anxiety is not None:
            prompt += f"Anxiety Level: {anxiety}/10\n"
        if stress is not None:
            prompt += f"Stress Level: {stress}/10\n"
        if sleep_hours:
            prompt += f"Sleep Duration: {sleep_hours} hours\n"
        if sleep_quality:
            prompt += f"Sleep Quality: {sleep_quality}\n"
        if journal:
            prompt += f"Journal Entry: {journal}\n"
        prompt += "\n"
    
    prompt += """Please provide:
    1. A summary of the overall mental well-being
    2. Identified patterns or concerns
    3. Personalized recommendations for improvement
    4. Positive reinforcement of good habits
    Please keep the tone supportive and encouraging."""

    try:
        # Configure Google Generative AI
    #os.environ['GOOGLE_API_KEY'] = "AIzaSyCBEOQfH0uTMjeJo1PEAUQ3ALxYxtMv3v8"

        genai.configure(api_key="AIzaSyCBEOQfH0uTMjeJo1PEAUQ3ALxYxtMv3v8")
        model = genai.GenerativeModel('gemini-pro')
        
        # Get response from the model
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Unable to generate insights at this time: {str(e)}"
def display_home():
    st.title("*:rainbow[Welcome to MoodLens]*")
    #add_bg_from_local("img.png")
    #st.image("RaipurRockets/brain.jpeg", width=300)
    st.write("""
    *:blue[MoodLens]* is a web application designed to help individuals track their *:blue[Mental Health]* over time. 
    By completing regular check-ins and recording their feelings, users can gain insights into their 
    emotional patterns and identify areas for improvement.
    """)
    
    st.header("*:rainbow[Features]*")
    col1, col2 ,col3 = st.columns(3 )
    
    with col1:
        st.write("1. Mental Health Check")
        st.write("2. Sleep Tracking") 
        st.write("3. Activity Tracking") 
        st.write("4. Journal Thoughts") 
    with col2:
       
        st.write("5. Meditation Timer")
        st.write("6. Goals")
        st.write("7. Check-in History")
        st.write("8. Insights")
    with col3:    
       
        st.write("9. Guidance")
        st.write("10. Game")
        st.write("11. ChatBot")           
def display_login():
    st.title("*:rainbow[Login]*")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")    
    if st.button("*:rainbow[Login]*"):
        if login_user(username, password):
            st.session_state.authentication_status = {
                'logged_in': True,
                'username': username
            }            
            st.success("Successfully logged in!")
            st.rerun()
        else:
            st.error("Invalid username or password")
def display_register():
    st.title("*:rainbow[Register]*")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")    
    if st.button("*:rainbow[Register]*"):
        if password != confirm_password:
            st.error("Passwords do not match!")
        elif register_user(username, password, email):
            st.success("Registration successful! Please login.")
            time.sleep(2)
            st.rerun()
        else:
            st.error("Username or email already exists!")
def mental_health_check():
    st.title("*:rainbow[Mental Health Check-in]*")
    
    if not st.session_state.authentication_status['logged_in']:
        st.warning("Please login to access this feature")
        return        
    username = st.session_state.authentication_status['username']    
    with st.form("mental_health_form"):
        mood = st.select_slider(
            "How are you feeling right now?",
            options=["Very Bad", "Bad", "Neutral", "Good", "Very Good"]
        )        
        anxiety = st.slider("Anxiety Level (0-10)", 0, 10, 5)
        stress = st.slider("Stress Level (0-10)", 0, 10, 5)
        notes = st.text_area("Would you like to write about your feelings?")        
        submitted = st.form_submit_button("Submit Check-in")        
        if submitted:
            conn = sqlite3.connect(DATABASE_PATH)
            c = conn.cursor()
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c.execute('''
                INSERT INTO mental_health_data 
                (username, data_type, mood, anxiety, stress, journal_entry, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, 'mental_health', mood, anxiety, stress, notes, current_time))            
            conn.commit()
            conn.close()            
            st.success("Mental health check-in recorded successfully!")
def sleep_tracking():
    st.title("*:rainbow[Sleep Tracking]*")
    if not st.session_state.authentication_status['logged_in']:
        st.warning("Please login to access this feature")
        return   
    username = st.session_state.authentication_status['username']
    with st.form("sleep_tracking_form"):
        sleep_hours = st.number_input("Hours of Sleep", 0.0, 24.0, 7.0, 0.5)
        sleep_quality = st.select_slider(
            "Sleep Quality",
            options=["Very Poor", "Poor", "Fair", "Good", "Excellent"]
        )
        notes = st.text_area("Any notes about your sleep?")    
        submitted = st.form_submit_button("Save Sleep Data")    
        if submitted:
            conn = sqlite3.connect(DATABASE_PATH)
            c = conn.cursor()        
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')        
            c.execute('''
                INSERT INTO mental_health_data 
                (username, data_type, sleep_hours, sleep_quality, journal_entry, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, 'sleep', sleep_hours, sleep_quality, notes, current_time))       
            conn.commit()
            conn.close()       
            st.success("Sleep data recorded successfully!")
def activity_tracking():
    st.title("*:rainbow[Activity Tracking]*")
    if not st.session_state.authentication_status['logged_in']:
        st.warning("Please login to access this feature")
        return       
    username = st.session_state.authentication_status['username']
    with st.form("activity_tracking_form"):  # Changed form name to match function
        activity_type = st.selectbox("Activity Type", 
                                ["Walking", "Running", "Cycling", "Yoga", "Other"])
        activity_duration = st.number_input("Duration (minutes)", min_value=1, max_value=1440)        
        notes = st.text_area("Notes (optional)")
        submitted = st.form_submit_button("Save Activity Data")       
        if submitted:
            conn = sqlite3.connect(DATABASE_PATH)
            c = conn.cursor()        
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')        
                   # Fixed SQL query - removed extra placeholders and added timestamp, intensity, notes
            c.execute('''
                INSERT INTO mental_health_data
                (username, data_type, activity_type,activity_duration,journal_entry, timestamp )
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, 'activity', activity_type,activity_duration,notes, current_time ))
                      
            conn.commit()
            conn.close()       
            st.success("Activity data saved!")  # Removed duplicate success message
def journal_Thoughts():
    st.title("*:rainbow[Journal Thoughts Entry]*")
    if not st.session_state.authentication_status['logged_in']:
        st.warning("Please login to access this feature")
        return       
    username = st.session_state.authentication_status['username']
    with st.form("Journal_tracking_form"):
        entry = st.text_area("Write Your Daily Thoughts...", height=200)
        submitted = st.form_submit_button("Save Activity Data")
        if submitted:
            conn = sqlite3.connect(DATABASE_PATH)
            c = conn.cursor()        
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')        
            
            # Fixed SQL query - removed extra placeholders and added timestamp, intensity, notes
            c.execute('''
                        INSERT INTO mental_health_data
                        (username, data_type, journal_entry, timestamp)
                        VALUES (?, ?, ?, ?)
                    ''', (username, 'journal', entry, current_time))
            conn.commit()
            conn.close()
            st.success("Journal  Thoughts entry saved!")
def meditation_timer():
    st.title("*:rainbow[Meditation Timer]*")
    if not st.session_state.authentication_status['logged_in']:
        st.warning("Please login to access this feature")
        return       
    username = st.session_state.authentication_status['username']
    with st.form("Journal_tracking_form"):
        duration = st.number_input("Meditation Duration (minutes)", 
                             min_value=1, 
                             max_value=60, 
                             value=1)
        if st.form_submit_button("Start Meditation"):
            st.snow()
            st.toast("§˜ Meditation session started! Œ")           
            total_seconds = duration * 60       
            # Create placeholder for timer display and progress bar
            timer_placeholder = st.empty()
            progress_bar = st.progress(0)
            timer_text = st.empty()        
            # Run the timer
            for remaining_seconds in range(total_seconds, -1, -1):
                # Calculate minutes and seconds for display
                mins = remaining_seconds // 60
                secs = remaining_seconds % 60                
                # Update timer display
                timer_placeholder.header(f"{mins:02d}:{secs:02d}")                
                # Update progress bar
                progress = (total_seconds - remaining_seconds) / total_seconds
                progress_bar.progress(progress)
                                # Add a pause between updates
                time.sleep(1)
                        # Show completion message
            timer_placeholder.header("*:blue[Meditation Complete!]* Ž‰")
            progress_bar.progress(1.0)
            time.sleep(1)                       
            st.success("Great job by completing your meditation session!")

            # Database operations
            conn = sqlite3.connect(DATABASE_PATH)
            c = conn.cursor()
            try:
                # Get current date
                current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                
                # Save meditation data
                c.execute('''
                    INSERT INTO mental_health_data 
                    (username, data_type, duration, timestamp) 
                    VALUES (?, ?, ?, ?)
                ''', (username, 'meditation', duration, current_date))
                conn.commit()
                st.success(f"Successfully saved your meditation session of {duration} minutes!")         
                # Update Statistics
                st.subheader("Meditation Statistics")
                                # Total meditation time
                c.execute('''
                    SELECT SUM(duration) 
                    FROM mental_health_data 
                    WHERE username = ? AND data_type = 'meditation'
                ''', (username,))
                total_time = c.fetchone()[0] or 0
                                # Average meditation time
                c.execute('''
                    SELECT AVG(duration) 
                    FROM mental_health_data 
                    WHERE username = ? AND data_type = 'meditation'
                ''', (username,))
                avg_time = c.fetchone()[0] or 0
                                # Number of sessions
                c.execute('''
                    SELECT COUNT(*) 
                    FROM mental_health_data 
                    WHERE username = ? AND data_type = 'meditation'
                ''', (username,))
                total_sessions = c.fetchone()[0] or 0
                # Display statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Meditation Time", f"{total_time:.0f} mins")
                with col2:
                    st.metric("Average Session Length", f"{avg_time:.1f} mins")
                with col3:
                    st.metric("Total Sessions", total_sessions)               
            except sqlite3.Error as e:
                st.error(f"Error saving data: {str(e)}")
            finally:
                conn.close()
def goals():
    st.title("*:rainbow[Goals]*")
    if not st.session_state.authentication_status['logged_in']:
        st.warning("Please login to access this feature")
        return    
    username = st.session_state.authentication_status['username']
    with st.form("Goals_tracking_form"):
        
        goal = st.text_area("Set a new goal")
        status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"]) 
        submitted = st.form_submit_button("Save Activity Data")
   
        if submitted:
            conn = sqlite3.connect(DATABASE_PATH)
            c = conn.cursor()
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
           # Fixed SQL query - removed extra placeholders and added timestamp, intensity, notes
            c.execute('''
                        INSERT INTO mental_health_data
                        (username, data_type, goal_description, goal_status, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (username, 'goal', goal, status, current_time))
            conn.commit()
            conn.close()
            st.success("Goal saved!")
def logout():
    st.session_state.authentication_status = {
        'logged_in': False,
        'username': None}
    st.rerun()      
if __name__ == "__main__": 
    init_db()
    main()
###### Packages Used ######
import streamlit as st # core package used in this project
import pandas as pd
import base64, random
import time,datetime
import pymysql
import os
import getpass
import socket
import secrets
import io,random
import plotly.express as px # to create visualisations at the admin session
import sqlitecloud
import spacy
import subprocess
import importlib.util
# libraries used to parse the pdf files
import nltk
nltk.data.path.append('./nltk_data')
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
from streamlit_tags import st_tags
from PIL import Image
# pre stored data for prediction purposes
from Courses import ds_course,web_course,android_course,ios_course,uiux_course,resume_videos,interview_videos
base_dir = os.path.dirname(__file__)
# Generates a link allowing the data in a given panda dataframe to be downloaded in csv format 

def get_csv_download_link(df,filename,text):
    csv = df.to_csv(index=False)
    ## bytes conversions
    b64 = base64.b64encode(csv.encode()).decode()      
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

# Reads Pdf file and check_extractable
def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    
    # file is a BytesIO stream
    for page in PDFPage.get_pages(file, caching=True, check_extractable=True):
        page_interpreter.process_page(page)
    
    text = fake_file_handle.getvalue()
    converter.close()
    fake_file_handle.close()
    return text

# show uploaded file path to view pdf_display
def show_pdf(file_path_or_obj):
    if isinstance(file_path_or_obj, str):
        with open(file_path_or_obj, "rb") as f:
            pdf_data = f.read()
    else:
        pdf_data = file_path_or_obj.read()  # for BytesIO

    base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# course recommendations which has data already loaded from Courses.py
def course_recommender(course_list):
    st.subheader("**Courses & Certificates Recommendations 👨‍🎓**")
    c = 0
    rec_course = []
    ## slider to choose from range 1-10
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course

# sql connector
connection = sqlitecloud.connect("sqlitecloud://cpzlbheynk.g2.sqlite.cloud:8860/cv?apikey=zSGLb725ClMGYsZ0rJ2qsWognqCJWitM108V3uBX8f4")
cursor = connection.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_data (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
    sec_token TEXT,
    host_name TEXT,
    dev_user TEXT,
    act_name TEXT,
    act_mail TEXT,
    act_mob TEXT,
    name TEXT,
    email TEXT,
    res_score TEXT,
    timestamp TEXT,
    no_of_pages TEXT,
    reco_field TEXT,
    cand_level TEXT,
    skills TEXT,
    recommended_skills TEXT,
    courses TEXT,
    pdf_name TEXT
);
''')

# Create user_feedback table
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_name TEXT,
    feed_email TEXT,
    feed_score TEXT,
    comments TEXT,
    timestamp TEXT
);
''')

# Commit changes and close
connection.commit()

# inserting miscellaneous data, fetched results, prediction and recommendation into user_data table
def insert_data(sec_token, host_name, dev_user, act_name, act_mail, act_mob,
                name, email, res_score, timestamp, no_of_pages,
                reco_field, cand_level, skills, recommended_skills,
                courses, pdf_name):
    DB_table_name = 'user_data'
    insert_sql = f"""
    INSERT INTO {DB_table_name}
    (sec_token, host_name, dev_user, act_name, act_mail, act_mob, name,
     email, res_score, timestamp, no_of_pages, reco_field, cand_level,
     skills, recommended_skills, courses, pdf_name)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    
    rec_values = (
        str(sec_token), host_name, dev_user, act_name, act_mail, act_mob,
        name, email, str(res_score), timestamp, str(no_of_pages),
        reco_field, cand_level, skills, recommended_skills, courses, pdf_name
    )
    cursor.execute(insert_sql, rec_values)
    connection.commit()


# inserting feedback data into user_feedback table
def insertf_data(feed_name, feed_email, feed_score, comments, Timestamp):
    DBf_table_name = 'user_feedback'
    insertfeed_sql = f"""
    INSERT INTO {DBf_table_name}
    (feed_name, feed_email, feed_score, comments, timestamp)
    VALUES (?, ?, ?, ?, ?)"""
    
    rec_values = (feed_name, feed_email, feed_score, comments, Timestamp)
    cursor.execute(insertfeed_sql, rec_values)
    connection.commit()


st.set_page_config(
   page_title="CVision",
   page_icon='./Logo/logo.jpeg',
)

def run():
    
    img = Image.open(os.path.join(base_dir, 'Logo', 'hq720.jpg'))
    st.image(img)
    st.sidebar.markdown(
        """
        <h1 style='
            text-align: center; 
            color: #6aa9ff; 
            font-weight: bold; 
            font-family: Trebuchet MS, sans-serif;
            letter-spacing: 1px;
        '>CVision</h1>
        """, 
        unsafe_allow_html=True
    )

    activities = ["User", "Feedback", "About", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)

    ###### CODE FOR CLIENT SIDE (USER) ######

    if choice == 'User':
        # Collecting Miscellaneous Information
        act_name = st.text_input('Name*')
        act_mail = st.text_input('Mail*')
        act_mob  = st.text_input('Mobile Number*')
        sec_token = secrets.token_urlsafe(12)
        host_name = socket.gethostname()
        dev_user = getpass.getuser()

        # Upload Resume
        st.markdown('''<h5 style='text-align: left; color: #4a6ee0;'> Upload Your Resume, And Get Smart Recommendations</h5>''',unsafe_allow_html=True)
        
        ## file upload in pdf format
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            with st.spinner('Hang On While We Cook Magic For You...'):
                time.sleep(4)
        
            os.makedirs('./Uploaded_Resumes', exist_ok=True)
            ### saving the uploaded resume to folder
            save_image_path = './Uploaded_Resumes/'+pdf_file.name
            pdf_name = pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)

            ### parsing and extracting whole resume 
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                
                ## Get the whole resume data into resume_text
                with open(save_image_path, 'rb') as file:
                    resume_text = pdf_reader(file)

                ## Showing Analyzed data from (resume_data)
                st.header("**Resume Analysis 🤘**")
                st.success("Hello " + str(resume_data.get('name', 'User')))
                st.subheader("**Your Basic info 👀**")
                try:
                    st.text('Name: '+resume_data['name'])
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                    st.text('Degree: '+str(resume_data['degree']))                    
                    st.text('Resume pages: '+str(resume_data['no_of_pages']))

                except:
                    pass
                ## Predicting Candidate Experience Level 
                resume_text_lower = resume_text.lower()
                ### Trying with different possibilities
                cand_level = ''
                if resume_data['no_of_pages'] is not None and resume_data['no_of_pages'] < 1:
                    cand_level = "NA"
                    st.markdown( '''<h4 style='text-align: left; color: #d73b5c;'>You are at Fresher level!</h4>''',unsafe_allow_html=True)
                
                #### if internship then intermediate level
                elif 'internship' in resume_text_lower or 'internships' in resume_text_lower:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',unsafe_allow_html=True)
                
                #### if Work Experience/Experience then Experience level
                elif 'experience' in resume_text_lower or 'work experience' in resume_text_lower:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',unsafe_allow_html=True)
                else:
                    cand_level = "Fresher"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at Fresher level!!''',unsafe_allow_html=True)

                ## Skills Analyzing and Recommendation
                st.subheader("**Skills Recommendation 💡**")
                
                ### Current Analyzed Skills
                keywords = st_tags(label='### Your Current Skills',
                text='See our skills recommendation below',value=resume_data['skills'],key = '1  ')

                ### Keywords for Recommendations
                ds_keyword = ['tensorflow','keras','pytorch','machine learning','deep Learning','flask','streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress','javascript', 'angular js', 'C#', 'Asp.net', 'flask', 'mysql', 'js', 'javascript', 'html', 'css', 'algorithms']
                android_keyword = ['android','android development','flutter','kotlin','xml','kivy']
                ios_keyword = ['ios','ios development','swift','cocoa','cocoa touch','xcode']
                uiux_keyword = ['ux','adobe xd','figma','zeplin','balsamiq','ui','prototyping','wireframes','storyframes','adobe photoshop','photoshop','editing','adobe illustrator','illustrator','adobe after effects','after effects','adobe premier pro','premier pro','adobe indesign','indesign','wireframe','solid','grasp','user research','user experience']
                n_any = ['english','communication','writing', 'microsoft office', 'leadership','customer management', 'social media']
                ### Skill Recommendations Starts                
                recommended_skills = []
                reco_field = ''
                rec_course = ''

                ### condition starts to check skills from keywords and predict field
                for i in resume_data['skills']:
                
                    #### Data science recommendation
                    if i.lower() in ds_keyword:
                        print(i.lower())
                        reco_field = 'Data Science'
                        st.success("** Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization','Predictive Analysis','Statistical Modeling','Data Mining','Clustering & Classification','Data Analytics','Quantitative Analysis','Web Scraping','ML Algorithms','Keras','Pytorch','Probability','Scikit-learn','Tensorflow',"Flask",'Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '2')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(ds_course)
                        break

                    #### Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        reco_field = 'Web Development'
                        st.success("** Our analysis says you are looking for Web Development Jobs **")
                        recommended_skills = ['React','Django','Node JS','React JS','php','laravel','Magento','wordpress','Javascript','Angular JS','c#','Flask','SDK']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '3')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(web_course)
                        break

                    #### Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        reco_field = 'Android Development'
                        st.success("** Our analysis says you are looking for Android App Development Jobs **")
                        recommended_skills = ['Android','Android development','Flutter','Kotlin','XML','Java','Kivy','GIT','SDK','SQLite']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '4')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(android_course)
                        break

                    #### IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        reco_field = 'IOS Development'
                        st.success("** Our analysis says you are looking for IOS App Development Jobs **")
                        recommended_skills = ['IOS','IOS Development','Swift','Cocoa','Cocoa Touch','Xcode','Objective-C','SQLite','Plist','StoreKit',"UI-Kit",'AV Foundation','Auto-Layout']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '5')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(ios_course)
                        break

                    #### Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        reco_field = 'UI-UX Development'
                        st.success("** Our analysis says you are looking for UI-UX Development Jobs **")
                        recommended_skills = ['UI','User Experience','Adobe XD','Figma','Zeplin','Balsamiq','Prototyping','Wireframes','Storyframes','Adobe Photoshop','Editing','Illustrator','After Effects','Premier Pro','Indesign','Wireframe','Solid','Grasp','User Research']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '6')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(uiux_course)
                        break

                    #### For Not Any Recommendations
                    elif i.lower() in n_any:
                        print(i.lower())
                        reco_field = 'NA'
                        st.warning("** Currently our tool only predicts and recommends for Data Science, Web, Android, IOS and UI/UX Development**")
                        recommended_skills = ['No Recommendations']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Currently No Recommendations',value=recommended_skills,key = '6')
                        st.markdown('''<h5 style='text-align: left; color: #092851;'>Maybe Available in Future Updates</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = "Sorry! Not Available for this Field"
                        break


                ## Resume Scorer & Resume Writing Tips
                st.subheader("**Resume Tips & Ideas 🥂**")
                res_score = 0
                
                ### Predicting Whether these key points are added to the resume

                if 'objective' in resume_text_lower or 'summary' in resume_text_lower:
                    res_score += 6
                    st.markdown("<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective/Summary</h5>", unsafe_allow_html=True)
                else:
                    st.markdown("<h5 style='text-align: left; color: #6aa9ff;'>[-] Please add your career objective, it will give your career intension to the Recruiters.</h5>", unsafe_allow_html=True)

                if any(word in resume_text_lower for word in ['education', 'school', 'college']):
                    res_score += 12
                    st.markdown("<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Education Details</h5>", unsafe_allow_html=True)
                else:
                    st.markdown("<h5 style='text-align: left; color: #6aa9ff;'>[-] Please add Education. It will give Your Qualification level to the recruiter</h5>", unsafe_allow_html=True)

                if 'experience' in resume_text_lower:
                    res_score += 16
                    st.markdown("<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Experience</h5>", unsafe_allow_html=True)
                else:
                    st.markdown("<h5 style='text-align: left; color: #6aa9ff;'>[-] Please add Experience. It will help you to stand out from crowd</h5>", unsafe_allow_html=True)

                if 'internship' in resume_text_lower:
                    res_score += 6
                    st.markdown("<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h5>", unsafe_allow_html=True)
                else:
                    st.markdown("<h5 style='text-align: left; color: #6aa9ff;'>[-] Please add Internships. It will help you to stand out from crowd</h5>", unsafe_allow_html=True)

                if 'skill' in resume_text_lower:
                    res_score += 7
                    st.markdown("<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h5>", unsafe_allow_html=True)
                else:
                    st.markdown("<h5 style='text-align: left; color: #6aa9ff;'>[-] Please add Skills. It will help you a lot</h5>", unsafe_allow_html=True)

                if 'hobbies' in resume_text_lower:
                    res_score += 4
                    st.markdown("<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies</h5>", unsafe_allow_html=True)
                else:
                    st.markdown("<h5 style='text-align: left; color: #6aa9ff;'>[-] Please add Hobbies. It will show your personality to the Recruiters and give the assurance that you are fit for this role or not.</h5>", unsafe_allow_html=True)

                if 'interests' in resume_text_lower or 'interest' in resume_text_lower:
                    res_score += 5
                    st.markdown("<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Interest</h5>", unsafe_allow_html=True)
                else:
                    st.markdown("<h5 style='text-align: left; color: #6aa9ff;'>[-] Please add Interest. It will show your interest other than job.</h5>", unsafe_allow_html=True)

                if 'achievements' in resume_text_lower or 'achievement' in resume_text_lower:
                    res_score += 13
                    st.markdown("<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements</h5>", unsafe_allow_html=True)
                else:
                    st.markdown("<h5 style='text-align: left; color: #6aa9ff;'>[-] Please add Achievements. It will show that you are capable for the required position.</h5>", unsafe_allow_html=True)

                if 'certification' in resume_text_lower:
                    res_score += 12
                    st.markdown("<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Certifications</h5>", unsafe_allow_html=True)
                else:
                    st.markdown("<h5 style='text-align: left; color: #6aa9ff;'>[-] Please add Certifications. It will show that you have done some specialization for the required position.</h5>", unsafe_allow_html=True)

                if 'project' in resume_text_lower:
                    res_score += 19
                    st.markdown("<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h5>", unsafe_allow_html=True)
                else:
                    st.markdown("<h5 style='text-align: left; color: #6aa9ff;'>[-] Please add Projects. It will show that you have done work related to the required position or not.</h5>", unsafe_allow_html=True)


                st.subheader("**Resume Score 📝**")
                
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )

                ### Score Bar
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(res_score):
                    score +=1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)

                ### Score
                st.success('** Your Resume Writing Score: ' + str(score)+'**')
                st.warning("** Note: This score is calculated based on the content that you have in your Resume. **")

                ### Getting Current Date and Time
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date+'_'+cur_time)


                ## Calling insert_data to add all the data into user_data                
                insert_data(str(sec_token), (host_name), (dev_user), (act_name), (act_mail), (act_mob), resume_data['name'], resume_data['email'], str(res_score), timestamp, str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']), str(recommended_skills), str(rec_course), pdf_name)

                ## Recommending Resume Writing Video
                st.header("**Bonus Video for Resume Writing Tips💡**")
                resume_vid = random.choice(resume_videos)
                st.video(resume_vid)

                ## Recommending Interview Preparation Video
                st.header("**Bonus Video for Interview Tips💡**")
                interview_vid = random.choice(interview_videos)
                st.video(interview_vid)

                ## On Successful Result 
                st.balloons()

            else:
                st.error('Something went wrong..')                


    ###### CODE FOR FEEDBACK SIDE ######
    elif choice == 'Feedback':   
        
        # timestamp 
        ts = time.time()
        cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        timestamp = str(cur_date+'_'+cur_time)

        # Feedback Form
        with st.form("my_form"):
            st.write("Feedback form")            
            feed_name = st.text_input('Name')
            feed_email = st.text_input('Email')
            feed_score = st.slider('Rate Us From 1 - 5', 1, 5)
            comments = st.text_input('Comments')
            Timestamp = timestamp        
            submitted = st.form_submit_button("Submit")
            if submitted:
                ## Calling insertf_data to add dat into user feedback
                insertf_data(feed_name,feed_email,feed_score,comments,Timestamp)    
                ## Success Message 
                st.success("Thanks! Your Feedback was recorded.") 
                ## On Successful Submit
                st.balloons()    


        # query to fetch data from user feedback table
        query = 'select * from user_feedback'        
        plotfeed_data = pd.read_sql(query, connection)                        


        # fetching feed_score from the query and getting the unique values and total value count 
        labels = plotfeed_data.feed_score.unique()
        values = plotfeed_data.feed_score.value_counts()


        # plotting pie chart for user ratings
        st.subheader("**Past User Rating's**")
        fig = px.pie(values=values, names=labels, title="Chart of User Rating Score From 1 - 5", color_discrete_sequence=px.colors.sequential.Aggrnyl)
        st.plotly_chart(fig)


        #  Fetching Comment History
        cursor.execute('select feed_name, comments from user_feedback')
        plfeed_cmt_data = cursor.fetchall()

        st.subheader("**User Comment's**")
        dff = pd.DataFrame(plfeed_cmt_data, columns=['User', 'Comment'])

        st.dataframe(dff, width=1000)

    
    ###### CODE FOR ABOUT PAGE ######
    elif choice == 'About':   

        st.subheader("**About The Tool - AI RESUME ANALYZER**")

        st.markdown('''

        <p align='justify'>
            A tool which parses information from a resume using natural language processing and finds the keywords, cluster them onto sectors based on their keywords. And lastly show recommendations, predictions, analytics to the applicant based on keyword matching.
        </p>

        <p align="justify">
            <b>How to use it: -</b> <br/><br/>
            <b>User -</b> <br/>
            In the Side Bar choose yourself as user and fill the required fields and upload your resume in pdf format.<br/>
            Just sit back and relax our tool will do the magic on it's own.<br/><br/>
            <b>Feedback -</b> <br/>
            A place where user can suggest some feedback about the tool.<br/><br/>
        </p><br/><br/>
        ''',unsafe_allow_html=True)  


    ###### CODE FOR ADMIN SIDE (ADMIN) ######
    else:
        st.success('Welcome to Admin Side')

        #  Admin Login
        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')

        if st.button('Login'):
            
            ## Credentials 
            if ad_user == 'admin' and ad_password == '12345':
                
                ### Fetch miscellaneous data from user_data(table) and convert it into dataframe
                cursor.execute('''SELECT ID, res_score, reco_field, cand_level FROM user_data''')
                datanalys = cursor.fetchall()
                plot_data = pd.DataFrame(datanalys, columns=['Idt', 'res_score', 'reco_field', 'User_Level'])
                
                ### Total Users Count with a Welcome Message
                values = plot_data.Idt.count()
                st.success("Welcome Nishant ! Total %d " % values + " User's Have Used Our Tool : )")                
                
                ### Fetch user data from user_data(table) and convert it into dataframe
                cursor.execute('''SELECT ID, sec_token, act_name, act_mail, act_mob, 
       reco_field, Timestamp, name, email, res_score, pdf_name, 
       cand_level, skills, Recommended_skills, courses, dev_user 
FROM user_data;''')
                data = cursor.fetchall()                

                st.header("**User's Data**")
                df = pd.DataFrame(data, columns=['ID', 'Token', 'name', 'Mail', 'Mobile Number', 'Predicted Field', 'Timestamp',
                                                 'Predicted name', 'Predicted Mail', 'Resume Score',  'File name',   
                                                 'User Level', 'Actual Skills', 'Recommended Skills', 'Recommended Course',
                                                   'Server User',])
                
                ### Viewing the dataframe
                st.dataframe(df)
                
                ### Downloading Report of user_data in csv file
                st.markdown(get_csv_download_link(df,'User_Data.csv','Download Report'), unsafe_allow_html=True)

                ### Fetch feedback data from user_feedback(table) and convert it into dataframe
                cursor.execute('''SELECT * from user_feedback''')
                data = cursor.fetchall()

                st.header("**User's Feedback Data**")
                df = pd.DataFrame(data, columns=['ID', 'name', 'Email', 'Feedback Score', 'Comments', 'Timestamp'])
                st.dataframe(df)

                ### query to fetch data from user_feedback(table)
                query = 'select * from user_feedback'
                plotfeed_data = pd.read_sql(query, connection)                        

                ### Analyzing All the Data's in pie charts

                # fetching feed_score from the query and getting the unique values and total value count 
                labels = plotfeed_data.feed_score.unique()
                values = plotfeed_data.feed_score.value_counts()
                
                # Pie chart for user ratings
                st.subheader("**User Rating's**")
                fig = px.pie(values=values, names=labels, title="Chart of User Rating Score From 1 - 5 🤗", color_discrete_sequence=px.colors.sequential.Aggrnyl)
                st.plotly_chart(fig)

                # fetching reco_field from the query and getting the unique values and total value count                 
                labels = plot_data.reco_field.unique()
                values = plot_data.reco_field.value_counts()
            else:
                st.error("Wrong ID & Password Provided")

# Calling the main (run()) function to make the whole process run
run()

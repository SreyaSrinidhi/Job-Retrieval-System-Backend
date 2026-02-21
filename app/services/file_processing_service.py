from werkzeug.datastructures import FileStorage

#TODO @jia @sreya - write resume parsing logic in here

#Note - for testing, can curl endpoint to pass file like this or similar:
#curl -X POST "http://127.0.0.1:5000/files/upload_resume"      -F "file=@D:/Documents/School/Career Development/ResumeRepo/Ethan Tobey SWE Resume(7.30.25).pdf"


def process_resume(resume: FileStorage):   #not super sure what the result this returns is right now - add when you guys determine
    print(f"resume being processed! {resume}")
    pass
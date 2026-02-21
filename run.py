from app import create_app

app = create_app()   #call factory function from app folder for better route organization

#TODO - make sure every function has typehints
#TODO - update readme once done with refactor

if __name__ == "__main__":
    # debug true so for someone reason it no work otherwise 
    app.run(debug=True)
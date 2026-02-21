from app import create_app

app = create_app()   #call factory function from app folder for better route organization

#TODO - make each service into an object - better encapsulation & organization
#TODO - update readme once done with refactor | maybe also create readmes in some modules to explain how they work?

if __name__ == "__main__":
    # debug true so for someone reason it no work otherwise 
    app.run(debug=True)
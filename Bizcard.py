
import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
import mysql.connector
import pandas as pd
from PIL import Image
import cv2
import os
import matplotlib.pyplot as plt 
import re
from pyngrok import ngrok





st.title("BizCardX: Extracting Business Card Data with OCR")

# creating option menu

selected =option_menu(None, ["Home", "upload & Extract", "Delete"],
                       icons= ["house", "cloud-upload", "pencil-square"],
                       default_index=0,
                       orientation="horizontal",
                       styles={"nav-link": {"font-size": "35px", "text-align": "centre", "margin": "-2px",
                                           "--hover-color": "#6495ED"},
                               "icon": {"font-size": "35px"},
                               "container": {"max-width": "6000px"},
                               "nav-link-selected": {"background-color": "#6495ED"}}) 

# INITIALIZING THE EasyOCR READER
reader = easyocr.Reader(['en'],gpu=False)

#SQL PORTION

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    database="Bizcard",
    password=""

 

)

print(mydb)
mycursor = mydb.cursor(buffered=True)

#mycursor.execute("create database Bizcard")

create_query1= ('''CREATE TABLE IF NOT EXISTS Bizcard.card_data_5
                   (id INT AUTO_INCREMENT PRIMARY KEY,
                    company_name VARCHAR(100),
                    card_holder VARCHAR(100),
                    designation VARCHAR(100),
                    mobile_number VARCHAR(50),
                    email VARCHAR(100),
                    website VARCHAR(100),
                    area VARCHAR(100),
                    city VARCHAR(100),
                    state VARCHAR(100),
                    pin_code VARCHAR(10),
                    image LONGBLOB
                    )''') 

mycursor.execute(create_query1)
mydb.commit()


#HOME MENU

if selected == "Home":
   col1,col2 = st.columns(2)
   with col1:
       st.image(Image.open("c:/Users/L/Desktop/Biz_project/pexels-johannes-plenio-1103970.jpg"), width=200)
       st.markdown("# :red[**Technologies used :**] Python,easy OCR, Streamlit. SQL, Pandas")
   with col2:
       st.write("## :blue[**About :**] Bizard is a python application designed to extract information from business card.")
       st.write('## The main purpose of Bizcard is to automate the process of extracting key details from business card images, such as the name, designation, company, contact information, and other relevant data. By leveraging the power of OCR (Optical Character Recognition) provided by EasyOCR, Bizcard is able to extract text from the images.')

#upload and extract menu

if selected == "upload & Extract":
    if st.button(":red[Already stored data]"):
       mycursor.execute("select  company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_data_5" )
       updated_df= pd.DataFrame(mycursor.fetchall(),
                                 columns= ["Company_Name", "Card_Holder", "Designation", "Mobile_Number",
                                           "Email",
                                           "Website", "Area", "City", "State", "Pin_Code"])
       st.write(updated_df)
    st.subheader(":black[Upload a Business Card]")
    uploaded_card= st.file_uploader ("upload here", label_visibility= "collapsed", type=["png", "jpeg", "jpg"]) 

    if uploaded_card is not None:
         def save_card(uploaded_card):
             uploaded_cards_dir = os.path.join(os.getcwd(), "uploaded_cards")

             #create the directory if it doesn't exist 
             os.makedirs(uploaded_cards_dir, exist_ok= True)

             with open(os.path.join(uploaded_cards_dir, uploaded_card.name), "wb") as f:
                 f.write(uploaded_card.getbuffer())

         save_card(uploaded_card)

         def image_preview(image, res):
            
             for (bbox, text, prob) in res:
                  #unpack the bounding box
                 (tl,tr,br,bl) = bbox
                 tl = (int(tl[0]), int(tl[1]))
                 tr = (int(tr[0]), int(tr[1]))
                 br = (int(br[0]), int(br[1]))
                 bl = (int(bl[0]), int(bl[1]))
                 cv2.rectangle(image,tl,br,(0,255,0), 2)
                 cv2.putText(image, text, (tl[0], tl[1] -10),
                             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,0), 2)
    
             return image
    
    

    #displaying the uploaded card

    col1,col2 = st.columns(2, gap = "large")
    with col1:
         st.markdown("#   ")
         st.markdown("#   ")
         st.markdown("### The picture of the uploaded card")
         st.image(uploaded_card) 

    #displaying the card with highlights
    
    with col2:
        st.markdown("#   ")
        st.markdown("#   ")
        with st.spinner("Please wait processing image.."):
             st.set_option('deprecation.showPyplotGlobalUse', False)
             saved_img = os.path.join(os.getcwd(), "uploaded_cards", uploaded_card.name)
             uploaded_cards_dir = os.path.join(os.getcwd(), "uploaded_cards")
             image= cv2.imread(saved_img)
             res = reader.readtext(saved_img)
             st.markdown("### Image Processed and Data Extracted")
             #st.pyplot(image_preview(image,res))
             modified_image = image_preview(image, res)
             st.image(modified_image)

#EASY OCR
    saved_img= os.path.join(os.getcwd(), "uploaded_cards" , uploaded_card.name)   
    result= reader.readtext(saved_img, detail=0, paragraph= False)   
             
# Converint image to binary to upload to SQL Database
             
    def img_to_binary(file):
         # Convert image data to binary format
         with open(file,'rb') as file:
              binaryData = file.read()
         return binaryData   
    

    data = {"company_name": [],
                "card_holder": [],
                "designation": [],
                "mobile_number": [],
                "email": [],
                "website": [],
                "area": [],
                "city": [],
                "state": [],
                "pin_code": [],
                "image": img_to_binary(saved_img)
                }

    def get_data(res):

        for ind, i in enumerate(res):
              # To get WEBSITE_URL
             if "www " in i.lower() or "www." in i.lower():
                 data["website"].append(i)
             elif "WWW" in i:
                 data["website"] = res[4] + "." + res[5]

               #to get email id
             elif "@" in i:
                  data["email"].append(i)

             #to get mobie num
             elif "-" in i:
                 data["mobile_number"].append(i)
                 if len(data["mobile_number"]) == 2:
                     data ["mobile_number"]= " & ".join(data["mobile_number"]) 

             #to get comapny name
             elif ind == len(res) - 1:
                   data["company_name"].append(i)   

            # to get card holder name
             elif ind == 0:
                  data["card_holder"]. append(i)

            #to get designation 
             elif ind == 1:
                  data["designation"] . append(i)   

             #to get area
             if re.findall('^[0-9].+, [a-zA-Z]+', i):
                  data["area"].append(i.split(",")[0])
             elif re.findall('[0-9] [a-zA-Z]+' , i): 
                  data["area"].append (i) 

            # to get city name

             match1 = re.findall('.+st , ([a-zA-Z]+).+', i)
             match2= re.findall('.+St,, ([a-zA-Z]+).+', i)
             match3= re.findall('^[E].*' , i)
             if match1:
                  data["city"].append(match1[0])
             elif match2:
                  data["city"].append(match2[0])
             elif match3:
                  data["city"].append(match3[0])

            # to get state
             state_match = re.findall('[a-zA-Z]{9} +[0-9]',i)   
             if state_match:
                 data["state"].append(i[:9])
             elif re.findall('^[0-9].+, ([a-zA-Z]+):', i):
                  data["state"].append(i.split()[-1])
             if len(data["state"]) ==2:
                 data["state"].pop(0) 

           #to get pincode 
             if len(i) >= 6 and i.isdigit():
                  data["pin_code"].append(i)
             elif re.findall('[a-zA-Z] {9} +[0-9]', i):
                  data["pin_code"].append(i[10:]) 

    
    get_data(result)

#Fuction to create dataframe 


    def create_df(data):
        
        lengths = [len(values) for values in data.values()]
        if not all(length == lengths[0] for length in lengths):
            max_length= max(lengths)
            for key, values in data.items():                                     
                if len(values) == 0:
                    data[key] = [''] * max_length
                elif isinstance(values, bytes):
                    data[key] = [''] * max_length

                else: 
                    data[key] = ''.join(data[key]) + ' ' * (max_length - len(values))
        
            
        

        df = pd.DataFrame(data)
        return df

    if "data" not in globals():
        data = {}  # Define an empty dictionary if data is not already defined

    for key, values in data.items():
        st.write(f"Length of '{key}': {len(values)}")  


    df  = create_df(data)
    st.success("### Data Extracted!")
                                                                  
  
 
                                                                                   
    if st.button("upload to Database"):

        insert_query =  '''INSERT INTO card_data_5(company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,image) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
        
        for i, row in df.iterrows():                                                   
        
           values = (row["company_name"],
                     row["card_holder"],
                     row["designation"],
                     row["mobile_number"],
                     row["email"],
                     row["website"],
                     row["area"],
                     row["city"],
                     row["state"],
                     row["pin_code"],
                     row["image"])

           
        mycursor.execute(insert_query,values)
        mydb.commit() 
        st.success("SAVED SUCCESSFULLY") 
          
          



if selected == "Delete":
    st.subheader(':blue[You can View , Delete the extracted data in Delete option ]')
    select = option_menu(None,
                              options= [ "DELETE"],
                              default_index=0,
                              orientation="horizontal",
                              styles={"container" : {"width" : "100%"},
                                        "nav-link": {"font-size" : "20px", "text-align" : "center", "margin": "-2px" },
                                        "nav-link-selected": {"background-color": "#6495ED"}})
    st.subheader(":red[Delete the data]")

     
    try:
        mycursor.execute("SELECT card_holder FROM card_data_5") 
        result = mycursor.fetchall()
        business_cards={}
        for row in result:
            business_cards[row[0]] = row[0]
        options = ["None"] + list(business_cards.keys())
        selected_card = st.selectbox("**Select a card**", options)
        if selected_card == "None":
           st.write("No card selected.")
        else:
            st.write(f"### You have selected :green[**{selected_card}'s**] card to delete")
            st.write("#### Proceed to delete this card?")
            if st.button("Yes Delete Business Card"):
               mycursor.execute(f"DELETE FROM card_data_5 WHERE card_holder='{selected_card}'")
               mydb.commit()
               st.success("Business card information deleted from database.") 


        if st.button(":blue[view updated data]"):
            mycursor.execute("select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_data_5")
            updated_df = pd.DataFrame(mycursor.fetchall(),
                                      columns = ["Company_Name", "Card_Holder", "Designation", "Mobile_Number",
                                                   "Email",
                                                   "Website", "Area", "City", "State", "Pin_Code"])
            st.write(updated_df)
    
    except:
            st.warning("There is no data available in the database")


            



#importing all libraries. For this program to work, all of these libraries needs to be available for use 
import csv
import requests
import json
import firebase_admin
from firebase_admin import db
from google.cloud import translate_v2 as translate 
from google_trans_new import google_translator 
import os
import tkinter as tk
from tkinter import ttk
from tkinter.constants import HORIZONTAL
import PIL.Image, PIL.ImageTk
import tkintermapview
import googlemaps
import time
import pykakasi
import math

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/theodoredacunha/Desktop/pbl3 coding/pbl3-352708-44699976758d.json"
address = "Minami Kusatsu Station"
data = {} #an empty dictionary that will store the data before pushing to database
usr_location =[]
API_KEY = "AIzaSyB22JoBKpzw1Z1DK1cSgPff1cdb9aGdwpM"
def saveToDatabase(categories): #transferring data from .csv file to the database
    map_client = googlemaps.Client(API_KEY)
    with open('/Users/theodoredacunha/Desktop/pbl3 coding/mock_data_v4.csv', mode='r') as csv_file: #open .csv file
        reader = csv.DictReader(csv_file) #turn .csv file to a dictionary
        hospitals = {} #empty array to store the hospital data for each category (it will reset for every category)
        current_cat = "" #the current category that is being worked on 
        counter = 0 #counts the number of hospitals in each categories 
        cat_counter = 0
        for i in reader:
            try:
                my_loc = map_client.geocode(i["Address"])
                my_lt_lng = my_loc[0]["geometry"]["location"]
                latitude = my_lt_lng["lat"]
                longitude = my_lt_lng["lng"]
            except:
                continue

            if(i["Category"] != current_cat):
                if current_cat != "":
                    cat_counter += 1
                    data[current_cat] = hospitals
                current_cat = i["Category"]
                hospitals = {}
                counter = 0
                hospitals["hospital" + str(counter)] = {"japanese_name": translate_to_japanese(i["Hospital Name"]), "japanese_address": translate_to_japanese(i["Address"]), "name": romanize_kanji(i["Hospital Name"]), "address": translate_to_english(i["Address"]), "longitude": longitude, "latitude": latitude, "english": i["Can the hospital speak English?"], "contact": i["telephone number"]}
            else:
                hospitals["hospital" + str(counter)] = {"japanese_name": translate_to_japanese(i["Hospital Name"]), "japanese_address": translate_to_japanese(i["Address"]), "name": romanize_kanji(i["Hospital Name"]), "address": translate_to_english(i["Address"]), "longitude": longitude, "latitude": latitude, "english": i["Can the hospital speak English?"], "contact": i["telephone number"]}
                
            print(hospitals["hospital" + str(counter)])
            counter += 1

        data[current_cat] = hospitals

        categories.set(data)

def maps_test(address, user_latlng): #finds the travel time between user and address (parameter)
    api_key = "AIzaSyB22JoBKpzw1Z1DK1cSgPff1cdb9aGdwpM" #api key for google maps api

    address_search = address.replace(" ", "%20") #replace space with "%20" in order to make it usable for URL

    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input="+ address_search + \
        "&inputtype=textquery&fields=name,formatted_address,permanently_closed&key="+ api_key #url of address being searched

    url_user_loc = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(user_latlng[0]) + "," + str(user_latlng[1]) + "&key=" + api_key #turning the user coordiantes to an address
    req = requests.get(url)
    response = req.json()["candidates"][0]["formatted_address"]
    response_user_loc = requests.get(url_user_loc).json()["results"][0]["formatted_address"]

    url_distance = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&" #url for distance matrix

    pro_user_loc = response_user_loc.replace(" ", "%20").lower()

    pro_des = response.replace(" ", "%20").lower()

    response_distance = requests.get(url_distance + "origins=" + pro_user_loc + "&destinations=" + pro_des + "&key=" + api_key).json() #get distance (travel time) between user and address


    results = response_distance["rows"][0]["elements"][0]["duration"]["text"] #results is in the form of text (e.g. 19 minutes, 59 minutes, etc.)
    
   
    ret = []
    ret.append(results)
    ret.append(int_convert(results))
    return ret

def int_convert(text):
    i = text.split(" ")
    if(len(i) == 4):
        num = i[0] * 60 + i[2]
    else:
        num = i[0]
    return num


def setupDB(): #connect to DB 
    cred_obj = firebase_admin.credentials.Certificate('/Users/theodoredacunha/Desktop/pbl3 coding/pbl3-project-firebase-adminsdk-h656x-5016a579b2.json')
    default_app = firebase_admin.initialize_app(cred_obj, {
	'databaseURL':'https://pbl3-project-default-rtdb.firebaseio.com'
    })

    categories = db.reference("/")

    return categories


def retrieveFromDatabase(categories, category): #retrieve hospital names from database. 
    hospitals = [] #will store all the retrieved hospitals
    

    getted_categories = categories.get() #get all possible categories from the database
    hospital_names = getted_categories[category] #extract hospitals from the category we want
    for i in hospital_names.keys(): #fill the hospitals list
        hospitals.append(hospital_names[i])

    return hospitals

def translate_to_english(text): #translate text to english (from japanese) 
    translate_client = translate.Client() 
    result = translate_client.translate(text, target_language="en")
    return(result["translatedText"])

def translate_to_japanese(text): #translate text to japanese (from english) 
    translate_client = translate.Client() 
    result = translate_client.translate(text, target_language="ja")
    return(result["translatedText"])

def romanize_kanji(text):
    kks = pykakasi.kakasi()
    result = kks.convert(text)
    romanized_version = ""
    for i in result:
        romanized_version += i["hepburn"].capitalize() + " "

    print(romanized_version)
    return romanized_version

def hospital_sort(hospital_list): #sort hospitals based on travel time
    hospital_list.sort(key = lambda x: x[4])
    return hospital_list



class App(tk.Tk):
    # 呪文
    def __init__(self, *args, **kwargs):
        # 呪文
        
        tk.Tk.__init__(self, *args, **kwargs)
        
        self.hospital_list = []
        self.user_latlng = [34.9815952, 135.9622613]
        self.progress_bar_len = 100
        self.location = address
        self.transportMode = "driving"
        self.marker_list = []
        # ウィンドウタイトルを決定
        self.title("Hospital Finder Application")
        self.API_KEY = "AIzaSyB22JoBKpzw1Z1DK1cSgPff1cdb9aGdwpM"
        self.gmaps = googlemaps.Client(self.API_KEY)
        # ウィンドウの大きさを決定
        self.geometry("360x640")

        # ウィンドウのグリッドを 1x1 にする
        # この処理をコメントアウトすると配置がズレる
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
#-----------------------------------main_frame-----------------------------
        # メインページフレーム作成
        self.main_frame = tk.Frame()
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        # フレーム1に移動するボタン
        self.Button1 = tk.Button(self.main_frame, text = "Internal Clinic", fg='black', width= 15, height = 10, command= lambda: (self.test(0)))
        self.Button2 = tk.Button(self.main_frame, text="Otorhinolaryngology", width= 15, height = 10, command= lambda: self.test(1))
        self.Button3 = tk.Button(self.main_frame, text="Ophtamologist", width= 15, height = 10, command= lambda: self.test(2))
        self.Button4 = tk.Button(self.main_frame, text="Obstetrics \n and \n Gynecology", width= 15, height = 10, command= lambda: self.test(3))
        self.Button5 = tk.Button(self.main_frame, text="Pediatric", width= 15, height = 10, command= lambda: self.test(4))
        self.Button6 = tk.Button(self.main_frame, text="Cardiology", width= 15, height = 10, command= lambda: self.test(5))
        self.changePageButton = tk.Button(self.main_frame, text="Settings", font=("",18), command=lambda : self.changePage(self.frame4), width= 29, height = 2)
        self.Button1.place(x=5, y=5)
        self.Button2.place(x=185, y=5)
        self.Button3.place(x=5, y=185)
        self.Button4.place(x=185, y=185)
        self.Button5.place(x=5, y=365)
        self.Button6.place(x=185, y=365)
        self.changePageButton.place(x=5, y=550)
#--------------------------------------------------------------------------
#-----------------------------------frame1---------------------------------
        # 移動先フレーム作成
        self.frame1 = tk.Frame()
        self.frame1.grid(row=0, column=0, sticky="nsew")
        # タイトルラベル作成
        self.map_widget = tkintermapview.TkinterMapView(self.frame1, width=360, height=320, corner_radius=0)
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        self.map_widget.place(relx=0.5, rely=0.5, anchor=tk.S)
        self.map_widget.set_position(self.user_latlng[0], self.user_latlng[1]) 
        self.map_widget.set_zoom(15)
        
        self.Button7 = tk.Button(self.frame1, text="Place1", font=("",12), width= 29, height = 2, command=lambda : self.changePage(self.frame3, 0))
        self.Button8 = tk.Button(self.frame1, text="Place2", font=("",12), width= 29, height = 2, command=lambda : self.changePage(self.frame3, 1))
        self.Button9 = tk.Button(self.frame1, text="Place3", font=("",12), width= 29, height = 2, command=lambda : self.changePage(self.frame3, 2))
        self.Button10 = tk.Button(self.frame1, text="Place4", font=("",12), width= 29, height = 2, command=lambda : self.changePage(self.frame3, 3))
        # フレーム1からmainフレームに戻るボタン
        self.back_button = tk.Button(self.frame1, text="Back", font=("",18), command=lambda : self.changePage(self.main_frame), width= 29, height = 4)
        self.Button7.place(x=50, y=340)
        self.Button8.place(x=50, y=400)
        self.Button9.place(x=50, y=460)
        self.Button10.place(x=50, y=520)
        self.back_button.place(x=2, y=580)
#--------------------------------------------------------------------------
#-----------------------------------frame2---------------------------------
        # 移動先フレーム作成
        self.frame2 = tk.Frame()
        self.frame2.grid(row=0, column=0, sticky="nsew")
        self.pb1 = ttk.Progressbar(self.frame2, orient=HORIZONTAL, length=30, mode='indeterminate')
        self.pb1.pack(expand=True)
#--------------------------------------------------------------------------

#-----------------------------------frame3---------------------------------
        # 移動先フレーム作成
        self.frame3 = tk.Frame()
        self.frame3.grid(row=0, column=0, sticky="nsew")
        self.HospitalNameText = tk.Label(self.frame3, text="English Name: \n")
        self.HospitalJapNameText = tk.Label(self.frame3, text="Japanese Name: \n")
        self.HospitalAddressText = tk.Label(self.frame3, text="English Address: \n")
        self.HospitalJapAddressText = tk.Label(self.frame3, text="Japanese Address: \n")
        self.TravelTime = tk.Label(self.frame3, text="Travel Time: \n")
        self.TransportModeText = tk.Label(self.frame3, text="Travel Mode: \n")
        self.EnglishAvailability = tk.Label(self.frame3, text="English Service Availability: \n")
        self.ContactInfo = tk.Label(self.frame3, text="Telephone Number: \n")

        self.HospitalNameText.pack()
        self.HospitalJapNameText.pack()
        self.HospitalAddressText.pack()
        self.HospitalJapAddressText.pack()
        self.TravelTime.pack()
        self.TransportModeText.pack()
        self.EnglishAvailability.pack()
        self.ContactInfo.pack()
        self.back_button = tk.Button(self.frame3, text="Back", font=("",18), command=lambda : self.changePage(self.frame1), width= 29, height = 4)
        self.back_button.place(x=2, y=580)
#--------------------------------------------------------------------------

#-----------------------------------frame4---------------------------------
        # 移動先フレーム作成
        self.frame4 = tk.Frame()
        self.option_transportMode = tk.StringVar(self)
        self.frame4.grid(row=0, column=0, sticky="nsew")
        self.LocationInputText = tk.Label(self.frame4, text="Enter Your Location: \n")
        self.LocationInput = tk.Entry(self.frame4)

        self.frame4.grid(row=0, column=0, sticky="nsew")
        self.TransportModeInputText = tk.Label(self.frame4, text="Enter Your Mode of Transport: \n")
        self.TransportModeInput = tk.OptionMenu(self.frame4, self.option_transportMode, "Driving", "Walking")

        self.LocationInputText.pack()
        self.LocationInput.pack()
        self.TransportModeInputText.pack()
        self.TransportModeInput.pack()

        self.save_settings = tk.Button(self.frame4, text="Save", font=("",18), command=lambda : (self.saveSettings(), self.changePage(self.main_frame)), width= 29, height = 4)
        self.save_settings.pack()
#--------------------------------------------------------------------------
        #main_frameを一番上に表示
        self.main_frame.tkraise()


    def saveSettings(self):
        self.location = self.LocationInput.get()
        self.transportMode = self.option_transportMode.get().lower()

    def changePage(self, page, current_preview_index=-1):
        '''
        画面遷移用の関数
        '''
        page.tkraise()
        if(page == self.frame1):
            for marker in self.marker_list:
                marker.delete()

            self.marker_list.append(self.map_widget.set_marker(self.user_latlng[0], self.user_latlng[1], text="You"))

            self.Button7["text"] = self.hospital_list[0][2]
            self.marker_list.append(self.map_widget.set_marker(self.hospital_list[0][4], self.hospital_list[0][3], text=self.hospital_list[0][2]))

            self.Button8["text"] = self.hospital_list[1][2]
            self.marker_list.append( self.map_widget.set_marker(self.hospital_list[1][4], self.hospital_list[1][3], text=self.hospital_list[1][2]))

            self.Button9["text"] = self.hospital_list[2][2]
            self.marker_list.append(self.map_widget.set_marker(self.hospital_list[2][4], self.hospital_list[2][3], text=self.hospital_list[2][2]))

            self.Button10["text"] = self.hospital_list[3][2]
            self.marker_list.append(self.map_widget.set_marker(self.hospital_list[3][4], self.hospital_list[3][3], text=self.hospital_list[3][2]))

        elif(page == self.frame3):
            self.HospitalNameText["text"] = "English Name: \n" + self.hospital_list[current_preview_index][2]
            self.HospitalJapNameText["text"] = "Japanese Name: \n" + self.hospital_list[current_preview_index][0]
            self.HospitalAddressText["text"] = "English Address: \n" + self.hospital_list[current_preview_index][5]
            self.HospitalJapAddressText["text"] = "Japanese Address: \n" + self.hospital_list[current_preview_index][1]
            self.TravelTime["text"] = "Travel Mode: \n" + str(math.floor(self.hospital_list[current_preview_index][6] / 60)) + " minutes " + str(self.hospital_list[current_preview_index][6] % 60) + " seconds"
            self.TransportModeText["text"] = "Transport Mode: \n" + self.transportMode
            
            
            if self.hospital_list[current_preview_index][7] == "1":
                self.EnglishAvailability["text"] = "English Service Availability: \n" + "Yes"
            else:
                self.EnglishAvailability["text"] = "English Service Availability: \n" + "No"

            self.ContactInfo["text"] = "Telephone Number: \n" + self.hospital_list[current_preview_index][8]
        elif(page == self.main_frame):
            for marker in self.marker_list:
                marker.delete()

    def get_user_coordinates(self):
        my_loc =  self.gmaps.geocode(self.location)
        my_lt_lng = my_loc[0]["geometry"]["location"]
        latitude = my_lt_lng["lat"]
        longitude = my_lt_lng["lng"]
        self.user_latlng = (latitude, longitude)

    def calc_distance(self, destination_coordinates):
        results = self.gmaps.distance_matrix(self.user_latlng, destination_coordinates, mode=self.transportMode)["rows"][0]["elements"][0]["duration"]["value"]
        return results

    def test(self, index):
        categories = ["Internal Clinic", "Obstetrics and Gynecology ", "Ophtamologist", "Cardiology", "Otorhinolaryngology", "Pediatric"]
        hospital = retrieveFromDatabase(refs, categories[index])
        self.pb1["length"] = len(hospital)
        self.get_user_coordinates()
        self.hospital_list = []
        for i in hospital:
                try:
                    distance = self.calc_distance((i["latitude"], i["longitude"]))
                    self.hospital_list.append([i["japanese_name"], i["japanese_address"], i["name"], i["longitude"], i["latitude"], i["address"], distance, i["english"], i["contact"]])
                except Exception as e:
                    print(e)
                    print("error has occured")
                    continue
                self.pb1["value"] += 1
        self.hospital_list = hospital_sort(self.hospital_list)
        print(self.user_latlng)
        self.map_widget.set_position(self.user_latlng[0], self.user_latlng[1])
        self.changePage(self.frame1)

if __name__ == "__main__":
    app = App()
    refs = setupDB()
    app.mainloop()
    #saveToDatabase(refs)



import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

from PIL import ImageTk, Image
import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import sys
import time
from datetime import datetime

class Gui_Functions:
    def __init__(self, items=None):
        self.s = items or []
        
        
    def createFolder(self, directory):
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
        except OSError:
            output.delete(0.0, tk.END)
            output.insert(tk.END, 'Error: Creating directory. ' +  directory)                 
   
    def find_mean_mode_median(self, df, filter1):
        df = df.sort_values('SCORE')
        self.mean = df.groupby([filter1, 
                                'YEAR'])['SCORE'].mean().round(2).reset_index()
        self.mean.name = 'MEAN'
        self.mode = df.groupby([filter1, 
                                'YEAR'])['SCORE'].agg(lambda x:x.value_counts().index[0]).reset_index()
        self.mode.name = 'MODE'
        self.median = df.groupby([filter1, 
                                  'YEAR'])['SCORE'].median().round(2).reset_index()
        self.median.name = 'MEDIAN'
        return self.mean, self.mode, self.median
   
    
    def load_file(self):
        path = filedialog.askopenfilename(title="Select File To Load", 
                                              filetypes=(("text files", "*.csv"), 
                                                         ("all files", "*.*")))
        filename = os.path.basename(path).replace('.csv', '')
        output.delete(0.0, tk.END)
        df = pd.read_csv(path)
        jsonfile = filename.lower() + '.json'
        jsonfile = './data/' + jsonfile
        df.to_json(jsonfile, indent = 4)
        message_load_file = 'LOAD COMPLETE - ' + filename + '.csv'
        output.insert(tk.END, message_load_file)
            
    def clean_data(self):
        try:
            df_ins = pd.read_json('./data/inspections.json')
            df_ins['PROGRAM STATUS'] = df_ins['PROGRAM STATUS'].replace('INACTIVE', 
                                                                        np.nan)
            df_ins = df_ins.dropna()
            # df_ins.to_json('inspections_cleaned.json', indent=4)
            df_ins['SEAT TYPE'] = np.nan
            df_pe = df_ins['PE DESCRIPTION']
            df_seat = df_pe.apply(lambda st: st[st.find("(")+1:st.find(")")])
            df_ins['SEAT TYPE'] = df_seat    
            df_ins['PE DESCRIPTION'] = df_pe.str.replace(r"\(.*\)","")
            df_activity = df_ins['ACTIVITY DATE']
            df_ins['YEAR'] = pd.DatetimeIndex(df_activity).year
            df_inspections_to_merge = df_ins[['FACILITY ID', 'SERIAL NUMBER',
                                              'FACILITY ZIP']]
            df_vio = pd.read_json('./data/violations.json')        
            df_vio_ins_merged = pd.merge(df_vio, 
                                         df_inspections_to_merge, 
                                         on='SERIAL NUMBER', how='outer')       
            self.df_vio_ins_merged = df_vio_ins_merged.drop_duplicates()
            self.df_ins = df_ins.drop_duplicates()
            df_ins.to_json('./data/inspections_cleaned.json', indent = 4)
            df_vio_ins_merged.to_json('./data/violations_merged.json', indent = 4)
            output.delete(0.0, tk.END)
            output.insert(tk.END, "CLEANING DATA COMPLETE")        
        except:
            output.delete(0.0, tk.END)
            output.insert(tk.END, "LOAD ALL CSV (*.csv) FILE'S BEFORE CLEANING")
            
    def load_clean_data(self):
        output.delete(0.0, tk.END)
        try:
            self.df_ins = pd.read_json('./data/inspections_cleaned.json') 
            self.df_vio_ins_merged = pd.read_json('./data/violations_merged.json')        
            output.insert(tk.END, "PREVIOUSLY CLEANED DATA LOADED")        
        except:
            output.insert(tk.END, "LOAD AND CLEAN DATA FIRST")
    
    def vendor_seating_score(self):
        try:           
            seat_type_mean, seat_type_mode, seat_type_median = self.find_mean_mode_median(self.df_ins, 
                                                                          'SEAT TYPE')
            output.delete(0.0, tk.END)
            output.insert(tk.END, seat_type_mean.to_string())  
            output.insert(tk.END, '\n\n')  
            output.insert(tk.END, seat_type_mode.to_string()) 
            output.insert(tk.END, '\n\n')  
            output.insert(tk.END, seat_type_median.to_string())   
            print(seat_type_mean.to_string(), seat_type_mode.to_string(),
                  seat_type_median.to_string())
        except:
            output.delete(0.0, tk.END)
            output.insert(tk.END, "LOAD AND CLEAN DATA BEFORE CALCULATING VENDOR SEATING SCORES")
            
    def zip_code_score(self):
        try:
            zipcode_mean, zipcode_mode, zipcode_median = self.find_mean_mode_median(self.df_ins, 
                                                                             'Zip Codes')
            output.delete(0.0, tk.END)
            output.insert(tk.END, zipcode_mean)  
            output.insert(tk.END, '\n\n')  
            output.insert(tk.END, zipcode_mode) 
            output.insert(tk.END, '\n\n')  
            output.insert(tk.END, zipcode_median)   
            print(zipcode_mean.to_string(), zipcode_mode.to_string(), 
                  zipcode_median.to_string())
            
        except:
            output.delete(0.0, tk.END)
            output.insert(tk.END, "LOAD AND CLEAN DATA BEFORE CALCULATING ZIP CODE SCORES")
    
    def plot_violation_number(self):
        try: 
            df = self.df_vio_ins_merged
            df1 = df[['FACILITY ID', 'VIOLATION CODE']]
            df1 = df1.drop_duplicates()    
            df_new = df1.groupby(['VIOLATION CODE']).count()
            df_new.columns = ['NUMBER OF ESTABLISHMENTS COMMITED']
            df_new['VIOLATION CODE'] = df_new.index
            df_new = df_new.sort_values('NUMBER OF ESTABLISHMENTS COMMITED', 
                                        ascending=False) 
            
            df_commited = df_new['NUMBER OF ESTABLISHMENTS COMMITED']
            
            data_over5000 = df_new[df_commited>5000]
            data_over5000.plot(kind ='barh', x = 'VIOLATION CODE', 
                y = 'NUMBER OF ESTABLISHMENTS COMMITED', color = 'red')
            
            plt.savefig('./data/plot.png', dpi=153)
            
            img = Image.open('./data/plot.png')
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(window, image = photo)
            label.image = photo
            label.grid(row=15, rowspan=6, columnspan=10, 
                       padx=(15,0), pady=(20,0))            
        except:
            output.delete(0.0, tk.END)
            output.insert(tk.END, "LOAD AND CLEAN DATA BEFORE PLOTTING") 
            
    def plot_correlation(self):
        try: 
            df = self.df_vio_ins_merged
            df1 = df[['FACILITY ID', 'VIOLATION CODE']]
            df1 = df1.drop_duplicates()    
            df_new = df1.groupby(['VIOLATION CODE']).count()
            df_new.columns = ['NUMBER OF ESTABLISHMENTS COMMITED']
            df_new['VIOLATION CODE'] = df_new.index
            df_new = df_new.sort_values('NUMBER OF ESTABLISHMENTS COMMITED', 
                                        ascending=False) 
            
            df_commited = df_new['NUMBER OF ESTABLISHMENTS COMMITED']
            
            data_over1 = df_new[df_commited>100]
            data_over1.plot(kind ='scatter', x = 'VIOLATION CODE', 
                y = 'NUMBER OF ESTABLISHMENTS COMMITED', color = 'green')
            
            plt.savefig('./data/plot2.png', dpi=153)
            
            img = Image.open('./data/plot2.png')
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(window, image = photo)
            label.image = photo
            label.grid(row=15, rowspan=6, columnspan=10, 
                       padx=(15,0), pady=(20,0))            
        except:
            output.delete(0.0, tk.END)
            output.insert(tk.END, "LOAD AND CLEAN DATA BEFORE PLOTTING")         
        

window = tk.Tk()
window.geometry("980x900")
window.title("DATA ANALYSIS TOOL")
window.configure(background='black')

gf = Gui_Functions()


# Creates a folder in the current directory called data
gf.createFolder('./data/')

# button to load file 
button_load = ttk.Button(window, 
                         text='\tLOAD FILE(*.csv)\t', 
                         command=gf.load_file).grid(row=0, 
                                               column=0, rowspan=1, 
                                               columnspan=1, padx=(15,0), 
                                               pady=(20,0), 
                                               sticky='NSEW')
# button to clean file
button_clean = ttk.Button(window, command=gf.clean_data, 
                         text='\tCLEAN DATA\t').grid(row=0, 
                                               column=1, rowspan=1, 
                                               columnspan=1, padx=(15,0), 
                                               pady=(20,0), 
                                               sticky='NSEW')     
 # button to load previosuly cleaned file                                              
button_load_cleaned_data = ttk.Button(window, command=gf.load_clean_data,
                         text='\tLOAD CLEANED FILE\t').grid(row=0, 
                                               column=3, rowspan=1, 
                                               columnspan=2, padx=(15,0), 
                                               pady=(20,0), 
                                               sticky='NSEW')     

inspectionScore_seat_text = '\tINSPECTION SCORE PER YEAR FOR VENDOR SEATING\t' 

# button to show INSPECTION SCORE PER YEAR FOR VENDOR SEATING
button_inspectionScore_seat = ttk.Button(window, command=gf.vendor_seating_score,
                         text=inspectionScore_seat_text).grid(row=1, 
                                               column=0, rowspan=1, 
                                               columnspan=2, padx=(15,0), 
                                               pady=(20,0), 
                                               sticky='NSEW')
                                                              
inspectionScore_zip_text = '\tINSPECTION SCORE PER YEAR FOR ZIP CODE\t'

# button to show INSPECTION SCORE PER YEAR FOR ZIP CODE
button_inspectionScore_zip = ttk.Button(window, command=gf.zip_code_score,
                         text=inspectionScore_zip_text).grid(row=2, 
                                               column=0, rowspan=1, 
                                               columnspan=2, padx=(15,0), 
                                               pady=(20,0), sticky='NSEW')

                                                             
                                                             
est_violation_text1 = 'PLOT: NUMBER OF ESTABLISHMENTS '
est_violation_text2 = 'vs TYPE OF VIOLATION'
est_violation_text = est_violation_text1 + est_violation_text2

# button to plot NUMBER OF ESTABLISHMENTS vs TYPE OF VIOLATION
button_est_violation = ttk.Button(window, command=gf.plot_violation_number,
                         text=est_violation_text).grid(row=4, 
                                               column=0, rowspan=1, 
                                               columnspan=4, padx=(15,0), 
                                               pady=(20,0), sticky='NSEW')

zip_violation_text1 = '\tPLOT: CORRELATION - NUMBER OF VIOLATIONS '
zip_violation_text2 = 'COMMITTED PER VENDOR vs THEIR ZIP CODE\t'
zip_violation_text = zip_violation_text1 + zip_violation_text2

#button to plot correlation NUMBER OF VIOLATIONS vs Zip Code
button_zip_violation = ttk.Button(window, command=gf.plot_correlation,
                         text=zip_violation_text).grid(row=5, 
                                               column=0, rowspan=1, 
                                               columnspan=4, padx=(15,0), 
                                               pady=(20,0), sticky='NSEW')
#

output = tk.Text(window, width=40, height=10, wrap='word', background='white')
output.grid(row=0, column=6, columnspan=3, rowspan=8, padx=(15,0), 
                                               pady=(20,0), sticky='NSEW')

window.mainloop()

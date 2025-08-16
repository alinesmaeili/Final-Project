# -*- coding: utf-8 -*-
"""
This script provides functions to read and parse hospital data from CSV files.

Note: Despite the filename, this script is designed to work with semicolon-delimited
CSV files ('Patients_DataBase.csv', 'Doctors_DataBase.csv'), not Excel (.xls/.xlsx)
files. It employs a manual, character-by-character parsing method to load patient
and doctor information into in-memory Python dictionaries for use by an application.
"""

def Read_Patients_DataBase() -> dict:
    """
    Reads patient data from "Patients_DataBase.csv" and structures it into a dictionary.

    This function manually parses the CSV file, assuming a fixed format where fields
    are separated by semicolons (;) and records (rows) are separated by newlines.
    The parsing is done character by character using a state machine (the 'flag' variable)
    to track the current column.

    Returns:
        A dictionary where each key is an integer Patient ID and the value is a list
        of patient attributes in the following order:
        [Department, Doctor_Name, Patient_Name, Patient_Age, Patient_Gender, Patient_Address, RoomNumber]
    """
    try:
        myfile = open("Patients_DataBase.csv", "r")
    except FileNotFoundError:
        print("Error: Patients_DataBase.csv not found.")
        return {}

    Patients_Dict = dict()
    # Temporary variables to build each field's value
    Patient_ID = ""
    Department = ""
    Doctor_Name = ""
    Patient_Name = ""
    Patient_Age = ""
    Patient_Gender = ""
    Patient_Address = ""
    RoomNumber = ""
    
    # The flag variable acts as a state machine to track the current column being parsed.
    # 0 = Patient_ID, 1 = Department, etc.
    flag = 0
    text = myfile.read()
    
    # Iterate through every character in the file content.
    for i in text:
        if flag == 0:
            if i != ";":
                Patient_ID += i
            else:
                flag = 1  # Move to the next field (Department)
                
        elif flag == 1:
            if i != ";":
                Department += i
            else:
                flag = 2  # Move to the next field (Doctor_Name)
                
        elif flag == 2:
            if i != ";":
                Doctor_Name += i
            else:
                flag = 3  # Move to the next field (Patient_Name)
                
        elif flag == 3:
            if i != ";":
                Patient_Name += i
            else:
                flag = 4  # Move to the next field (Patient_Age)
                
        elif flag == 4:
            if i != ";":
                Patient_Age += i
            else:
                flag = 5  # Move to the next field (Patient_Gender)
                
        elif flag == 5:
            if i != ";":
                Patient_Gender += i
            else:
                flag = 6  # Move to the next field (Patient_Address)
                
        elif flag == 6:
            if i != ";":
                Patient_Address += i
            else:
                flag = 7  # Move to the final field (RoomNumber)
                
        elif flag == 7:
            if i != "\n":
                RoomNumber += i
            else:  # A newline character signifies the end of a record.
                # Add the complete record to the dictionary.
                Patients_Dict[int(Patient_ID)] = [Department, Doctor_Name, Patient_Name, Patient_Age, Patient_Gender, Patient_Address, RoomNumber]
                # Reset all temporary variables for the next line.
                Patient_ID = ""
                Department = ""
                Doctor_Name = ""
                Patient_Name = ""
                Patient_Age = ""
                Patient_Gender = ""
                Patient_Address = ""
                RoomNumber = ""
                flag = 0  # Reset the flag to start with the first field of the next record.
                
    myfile.close()
    return Patients_Dict
            
            
            
def Read_Doctors_DataBase() -> dict:
    """
    Reads doctor and appointment data from "Doctors_DataBase.csv".

    This function uses a manual parsing method to handle a complex CSV structure where
    each line contains a doctor's primary information followed by a variable number of
    appointments. It expects semicolons (;) as delimiters. A pre-processing step is
    included to handle potential empty fields by replacing ';;' with ';'.

    Returns:
        A dictionary where each key is an integer Doctor ID. The value is a list
        containing the doctor's details as the first element, followed by one list
        for each of their appointments.
        Example structure:
        {Doctor_ID: [[Dept, Name, Address], [Patient_ID_1, Start_1, End_1], [Patient_ID_2, Start_2, End_2]]}
    """
    try:
        myfile = open("Doctors_DataBase.csv", "r")
    except FileNotFoundError:
        print("Error: Doctors_DataBase.csv not found.")
        return {}

    Doctors_Dict = dict()
    # Temporary variables for parsing
    Doctor_ID = ""
    Department = ""
    Doctor_Name = ""
    Doctor_Address = ""
    Patient_ID = ""
    Session_Start = ""
    Session_End = ""
    
    # Flag to track the current parsing state.
    flag = 0
    text = myfile.read()

    # Pre-processing step: Replace double semicolons (likely for empty fields) with single ones.
    while text.count(";;"):
        text = text.replace(";;", ";")
    
    for i in text:
        if flag == 0:
            if i != ";":
                Doctor_ID += i
            else:
                flag = 1  # Move to Department
                
        elif flag == 1:
            if i != ";":
                Department += i
            else:
                flag = 2  # Move to Doctor_Name
                
        elif flag == 2:
            if i != ";":
                Doctor_Name += i
            else:
                flag = 3  # Move to Doctor_Address
                
        elif flag == 3:
            if i != ";":
                Doctor_Address += i
            else:
                flag = 4  # Move to parsing appointments
                # Create the main entry for the doctor and add their personal data list.
                Doctor_Data_List = [Department, Doctor_Name, Doctor_Address]
                Doctors_Dict[int(Doctor_ID)] = [Doctor_Data_List]
                        
        elif flag == 4:
            if i not in (";", "\n"):
                Patient_ID += i
            elif i == ";":
                flag = 5  # Move to Session_Start
            elif i == "\n":
                # End of line, reset for the next doctor.
                flag = 0
                Doctor_ID, Department, Doctor_Name, Doctor_Address = "", "", "", ""
                        
        elif flag == 5:
            if i != ";":
                Session_Start += i
            else:
                flag = 6  # Move to Session_End
        
        elif flag == 6:
            if i not in (";", "\n"):
                Session_End += i
            elif i == ";":
                # End of an appointment, add it to the doctor's record.
                Appointment_List = [int(Patient_ID), Session_Start, Session_End]
                Doctors_Dict[int(Doctor_ID)].append(Appointment_List)
                # Reset appointment variables and return to parsing the next Patient_ID.
                Patient_ID, Session_Start, Session_End = "", "", ""
                flag = 4
            elif i == "\n":
                # End of the line and the final appointment for this doctor.
                flag = 0
                Doctor_ID, Department, Doctor_Name, Doctor_Address = "", "", "", ""

    myfile.close()
    return Doctors_Dict

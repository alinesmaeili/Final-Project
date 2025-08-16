# -*- coding: utf-8 -*-
"""
This script provides functions for writing hospital data back to CSV files.

It serves as the counterpart to 'Read_Hospital_Excel_Sheet.py'. These functions
take Python dictionaries containing patient or doctor data and serialize them into
the specific semicolon-delimited format required by the application, overwriting the
existing files ('Patients_DataBase.csv', 'Doctors_DataBase.csv').
"""

def Write_Patients_DataBase(Patients_DataBase: dict):
    """
    Writes a dictionary of patient data to "Patients_DataBase.csv".

    This function takes a dictionary, where each key is a patient ID, and writes
    the associated patient information as a new line in the CSV file. The file is
    overwritten with the new data.

    Args:
        Patients_DataBase: A dictionary with the expected format:
            { Patient_ID (int): [
                Department (str),
                Doctor_Name (str),
                Patient_Name (str),
                Patient_Age (str),
                Patient_Gender (str),
                Patient_Address (str),
                RoomNumber (str)
              ], ...
            }
    """
    # Open the file in 'w' (write) mode, which overwrites the existing file.
    with open("Patients_DataBase.csv", "w") as myfile:
        # Iterate through each patient ID (key) in the dictionary.
        for patient_id in Patients_DataBase:
            # Get the list of patient details for the current ID.
            details = Patients_DataBase[patient_id]
            # Construct the semicolon-delimited string and write it to the file.
            line = (
                f"{patient_id};{details[0]};{details[1]};{details[2]};"
                f"{details[3]};{details[4]};{details[5]};{details[6]}\n"
            )
            myfile.write(line)

def Write_Doctors_DataBase(Doctors_DataBase: dict):
    """
    Writes a dictionary of doctor and appointment data to "Doctors_DataBase.csv".

    This function serializes a complex dictionary structure into the specific,
    single-line format required for each doctor. It writes the doctor's personal
    details followed by all their appointments, all on the same line and separated
    by semicolons.

    Args:
        Doctors_DataBase: A dictionary with the expected nested list structure:
            { Doctor_ID (int): [
                [Department (str), Doctor_Name (str), Doctor_Address (str)],
                [Patient_ID_1 (int), Session_Start_1 (str), Session_End_1 (str)],
                [Patient_ID_2 (int), Session_Start_2 (str), Session_End_2 (str)],
                ...
              ], ...
            }
    """
    # Open the file in 'w' (write) mode to overwrite its contents.
    with open("Doctors_DataBase.csv", "w") as myfile:
        # Iterate through each doctor ID (key) in the dictionary.
        for doctor_id in Doctors_DataBase:
            # Start the line with the doctor's ID.
            line = f"{doctor_id};"
            
            # The value is a list containing the doctor's details and their appointments.
            # Iterate through this list of lists.
            for item in Doctors_DataBase[doctor_id]:
                # Append each element of the inner list (details or appointment)
                # to the line, followed by a semicolon.
                line += f"{item[0]};{item[1]};{item[2]};"
            
            # Write the completed line for the doctor to the file.
            myfile.write(line + "\n")

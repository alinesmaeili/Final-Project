# -*- coding: utf-8 -*-
"""
This is the main executable script for the Command-Line Hospital Management System.

It serves as the user interface, providing a menu-driven system for interacting
with hospital data. The system has two primary modes:
1.  Admin Mode: A password-protected area that allows for full CRUD (Create, Read,
    Update, Delete) operations on patient records, doctor records, and appointments.
2.  User Mode: A read-only mode that allows users to view general hospital
    information, such as department lists, doctor details, and appointments.

The application relies on two helper modules:
- `Read_Hospital_Excel_Sheet`: For loading patient and doctor data from CSV files
  into memory at the start of operations.
- `Write_Hospital_Excel_Sheet`: For saving any changes made during an admin session
  back to the CSV files, ensuring data persistence.
"""

# --- Local Module Imports ---
# These custom modules handle the reading and writing of data from/to the CSV files.
import Read_Hospital_Excel_Sheet
import Write_Hospital_Excel_Sheet

	
def AppointmentIndexInDoctorsDataBase (patient_ID) :
	"""
    Finds a patient's appointment within the nested Doctors_DataBase dictionary.

    This helper function iterates through all doctors and their scheduled appointments
    to locate a specific appointment by the patient's ID.

    Args:
        patient_ID: The integer ID of the patient whose appointment is to be found.

    Returns:
        A tuple containing two elements:
        - The index of the appointment in the doctor's appointment list.
        - The ID of the doctor with whom the appointment is scheduled.
    Returns:
        None if no appointment is found for the given patient ID.
    """
	# Iterate through each doctor's ID in the Doctors database.
	for i in Doctors_DataBase :
		# For each doctor, iterate through their list of details and appointments.
		for j in Doctors_DataBase[i] :							
			# Check if the first element of the sublist matches the patient ID.
			# This works because the doctor's details list starts with a string (Department),
			# while appointment lists start with an integer patient ID.
			if str(patient_ID) == str(j[0]) :
				# If a match is found, get the index of this appointment list.
				Appointment_index = Doctors_DataBase[i].index(j)
				# Return the index and the doctor's ID.
				return Appointment_index,i

# --- Main Application ---

# Display the welcome banner.
print("****************************************************************************")
print("*                                                                          *")
print("*                   Welcome Hospital Management System                     *")
print("*                                                                          *")
print("****************************************************************************")
	
	
# --- Main Program Loop ---
# This loop continues until the password check is failed three times,
# which sets the `tries_flag` to exit the program.
tries = 0
tries_flag = ""
while tries_flag != "Close the program" :

		# Load the most current data from the CSV files at the beginning of each loop.
		# This ensures that any changes from a previous admin session are reflected.
		Pateints_DataBase = Read_Hospital_Excel_Sheet.Read_Patients_DataBase()
		Doctors_DataBase  = Read_Hospital_Excel_Sheet.Read_Doctors_DataBase()
				
		# --- Mode Selection ---
		print("-----------------------------------------")
		print("|Enter 1 for Admin mode			|\n|Enter 2 for user mode			|")
		print("-----------------------------------------")
		Admin_user_mode = input("Enter your mode : ") 
		

		# =================================================================================
		# --- Admin Mode ---
		# =================================================================================
		if Admin_user_mode == "1" :
				print("*****************************************\n|         Welcome to admin mode         |\n*****************************************")
				Password = input("Please enter your password : ")
				
				# This inner loop handles all actions within the Admin Mode.
				while True :
					
					# --- Password Check ---
					if Password == "1234" :
						print("-----------------------------------------")
						print("|To manage patients Enter 1 		|\n|To manage docotrs Enter 2	 	|\n|To manage appointments Enter 3 	|\n|To be back Enter E			|")
						print("-----------------------------------------")
						AdminOptions = input ("Enter your choice : ")
						AdminOptions = AdminOptions.upper()
						
						# --- Admin Menu: Patient Management ---
						if AdminOptions == "1" :
								print("-----------------------------------------")
								print("|To add new patient Enter 1	  	|")
								print("|To display patient Enter 2	  	|")
								print("|To delete patient data Enter 3		|")
								print("|To edit patient data Enter 4    	|")
								print("|To Back enter B      			|")
								print("-----------------------------------------")
								Admin_choice = input ("Enter your choice : ")
								Admin_choice = Admin_choice.upper()
								
								# --- 1.1: Add New Patient ---
								if Admin_choice == "1" :
											# Use a try-except block to prevent crashes from non-integer input.
											try :
												patient_ID = int(input("Enter patient ID : "))
												# Ensure the chosen patient ID is not already in use.
												while patient_ID in Pateints_DataBase :
													patient_ID = int(input("This ID is unavailable, please try another ID : "))					
												Department=input("Enter patient department                : ")
												DoctorName=input("Enter name of doctor following the case : ")
												Name      =input("Enter patient name                      : ")
												Age       =input("Enter patient age                       : ")
												Gender    =input("Enter patient gender                    : ")
												Address   =input("Enter patient address                   : ")
												RoomNumber=input("Enter patient room number               : ")
												# Add the new patient to the dictionary.
												Pateints_DataBase[patient_ID]=[Department,DoctorName,Name,Age,Gender,Address,RoomNumber]
												print("----------------------Patient added successfully----------------------")
											except :
												print("Patient ID should be an integer number")
										
								# --- 1.2: Display Patient Data ---
								elif Admin_choice == "2" :
											try :
												patient_ID = int(input("Enter patient ID : "))
												# Ensure the patient ID exists before trying to access it.
												while patient_ID not in Pateints_DataBase :
													patient_ID = int(input("Incorrect ID, Please Enter patient ID : "))
												print("\npatient name        : ",Pateints_DataBase[patient_ID][2])
												print("patient age         : ",Pateints_DataBase[patient_ID][3])
												print("patient gender      : ",Pateints_DataBase[patient_ID][4])
												print("patient address     : ",Pateints_DataBase[patient_ID][5])
												print("patient room number : ",Pateints_DataBase[patient_ID][6])
												print("patient is in "+Pateints_DataBase[patient_ID][0]+" department")
												print("patient is followed by doctor : "+Pateints_DataBase[patient_ID][1])
											except :
												print("Patient ID should be an integer number")
								
								# --- 1.3: Delete Patient Data ---
								elif Admin_choice == "3" :
											try :
												patient_ID = int(input("Enter patient ID : "))
												while patient_ID not in Pateints_DataBase :
													patient_ID = int(input("Incorrect ID, Please Enter patient ID : "))
												# Remove the patient record using the pop method.
												Pateints_DataBase.pop(patient_ID)
												print("----------------------Patient data deleted successfully----------------------")
											except :
												print("Patient ID should be an integer number")
										
								# --- 1.4: Edit Patient Data ---
								elif Admin_choice == "4" :
											try :
												patient_ID=int(input("Enter patient ID : "))
												while patient_ID not in Pateints_DataBase :
													patient_ID = int(input("Incorrect ID, Please Enter patient ID : "))
												# A sub-menu for editing specific fields of a patient's record.
												while True :
													print("------------------------------------------")
													print("|To Edit pateint Department Enter 1 :    |")
													print("|To Edit Doctor following case Enter 2 : |")
													print("|To Edit pateint Name Enter 3 :          |")
													print("|To Edit pateint Age Enter 4 :           |")
													print("|To Edit pateint Gender Enter 5 :        |")
													print("|To Edit pateint Address Enter 6 :       |")
													print("|To Edit pateint RoomNumber Enter 7 :    |")
													print("|To be Back Enter B                      |")
													print("-----------------------------------------")
													Admin_choice = input("Enter your choice : ")
													Admin_choice = Admin_choice.upper()
													if Admin_choice == "1" :
														Pateints_DataBase[patient_ID][0]=input("\nEnter patient department : ")
														print("----------------------Patient Department edited successfully----------------------")
														
													elif Admin_choice == "2" :
														Pateints_DataBase[patient_ID][1]=input("\nEnter Doctor follouing case : ")
														print("----------------------Doctor follouing case edited successfully----------------------")
										
													elif Admin_choice == "3" :
														Pateints_DataBase[patient_ID][2]=input("\nEnter patient name : ")
														print("----------------------Patient name edited successfully----------------------")
													
													elif Admin_choice == "4" :
														Pateints_DataBase[patient_ID][3]=input("\nEnter patient Age : ")
														print("----------------------Patient age edited successfully----------------------")
												
													elif Admin_choice == "5" :
														Pateints_DataBase[patient_ID][4]=input("\nEnter patient gender : ")
														print("----------------------Patient address gender successfully----------------------")
														
													elif Admin_choice == "6" :
														Pateints_DataBase[patient_ID][5]=input("\nEnter patient address : ")
														print("----------------------Patient address edited successfully----------------------")
														
													elif Admin_choice == "7" :
														Pateints_DataBase[patient_ID][6]=input("\nEnter patient RoomNumber : ")
														print("----------------------Patient RoomNumber edited successfully----------------------")
												
													elif Admin_choice == "B" :
														# Break from the inner edit loop to go back to the patient menu.
														break
														
													else :
														print("Please Enter a correct choice")
											except :
												print("Patient ID should be an integer number")
																				
								# --- 1.5: Back ---
								elif Admin_choice == "B" :
											# Break from the patient management loop to go back to the main admin menu.
											break
								
								else :
											print("Please enter a correct choice\n")
											
						# --- Admin Menu: Doctor Management ---
						elif AdminOptions == "2" :
							print("-----------------------------------------")
							print("|To add new doctor Enter 1              |")
							print("|To display doctor Enter 2              |")
							print("|To delete doctor data Enter 3          |")
							print("|To edit doctor data Enter 4            |")
							print("|To be back enter B                     |")
							print("-----------------------------------------")
							Admin_choice = input ("Enter your choice : ")
							Admin_choice = Admin_choice.upper()
							
							# --- 2.1: Add New Doctor ---
							if Admin_choice == "1" :
									try :
										Doctor_ID = int(input("Enter doctor ID : "))
										while Doctor_ID in Doctors_DataBase :
											Doctor_ID = int(input("This ID is unavailable, please try another ID : "))
										
										Department=input("Enter Doctor department : ")
										Name      =input("Enter Doctor name       : ")
										Address   =input("Enter Doctor address    : ")
										# Adds the doctor's details as a nested list.
										Doctors_DataBase[Doctor_ID]=[[Department,Name,Address]]
										print("----------------------Doctor added successfully----------------------")
									except :
										print("Doctor ID should be an integer number")
								
							# --- 2.2: Display Doctor Data ---
							elif Admin_choice == "2" :
									try :
										Doctor_ID = int(input("Enter doctor ID : "))
										while Doctor_ID not in Doctors_DataBase :
											Doctor_ID = int(input("Incorrect ID, Please Enter doctor ID : "))
										print("Doctor name    : ",Doctors_DataBase[Doctor_ID][0][1])
										print("Doctor address : ",Doctors_DataBase[Doctor_ID][0][2])
										print("Doctor is in "+Doctors_DataBase[Doctor_ID][0][0]+" department")
									except :
										print("Doctor ID should be an integer number")
							
							# --- 2.3: Delete Doctor Data ---
							elif Admin_choice == "3" :
									try :
										Doctor_ID = int(input("Enter doctor ID : "))
										while Doctor_ID not in Doctors_DataBase :
											Doctor_ID = int(input("Incorrect ID, Please Enter doctor ID : "))
										Doctors_DataBase.pop(Doctor_ID)
										print("/----------------------Doctor data deleted successfully----------------------/")
									except :
										print("Doctor ID should be an integer number")

							# --- 2.4: Edit Doctor Data ---
							elif Admin_choice == "4" :
									try :	
										Doctor_ID=input("Enter doctor ID : ")
										while Doctor_ID not in Doctors_DataBase :
											Doctor_ID = int(input("Incorrect ID, Please Enter doctor ID : "))
										print("-----------------------------------------")
										print("|To Edit doctor's department Enter 1    |")
										print("|To Edit doctor's name Enter 2          |")
										print("|To Edit doctor's address Enter 3       |")
										print("To be Back Enter B                      |")
										print("-----------------------------------------")
										Admin_choice=input("Enter your choice : ")
										Admin_choice = Admin_choice.upper()
										if Admin_choice == "1" :
											Doctors_DataBase[Doctor_ID][0][0]=input("Enter Doctor's Department : ")
											print("/----------------------Doctor's department edited successfully----------------------/")
											
										elif Admin_choice == "2" :
											Doctors_DataBase[Doctor_ID][0][1]=input("Enter Doctor's Name : ")
											print("----------------------Doctor's name edited successfully----------------------")
											
										elif Admin_choice == "3" :
											Doctors_DataBase[Doctor_ID][0][2]=input("Enter Doctor's Address : ")
											print("----------------------Doctor's address edited successfully----------------------")
										
										elif Admin_choice == "B" :
											break
										
										else :
											print("\nPlease enter a correct choice\n")
											
									except :
										print("Doctor ID should be an integer number")
											
							# --- 2.5: Back ---
							elif Admin_choice == "B" :
										break
									
							else :
								print("\nPlease enter a correct choice\n")
											
						# --- Admin Menu: Appointment Management ---
						elif AdminOptions == "3" :
							print("-----------------------------------------")
							print("|To book an appointment Enter 1         |")
							print("|To edit an appointment Enter 2         |")
							print("|To cancel an appointment Enter 3       |")
							print("|To be back enter B                     |")
							print("-----------------------------------------")
							Admin_choice = input ("Enter your choice : ")
							Admin_choice = Admin_choice.upper()

							# --- 3.1: Book an Appointment ---
							if Admin_choice == "1" :							
								try :
										Doctor_ID = int(input("Enter the ID of doctor : "))
										while Doctor_ID not in Doctors_DataBase :
											Doctor_ID = int(input("Doctor ID incorrect, Please enter a correct doctor ID : "))
										print("---------------------------------------------------------")
										print("|For book an appointment for an exist patient Enter 1   |\n|For book an appointment for a new patient Enter 2      |\n|To be Back Enter B                                     |")
										print("---------------------------------------------------------")
										Admin_choice = input ("Enter your choice : ")
										Admin_choice = Admin_choice.upper()
										
										# Option to book for an existing patient.
										if Admin_choice == "1" :
												patient_ID = int(input("Enter patient ID : "))
												while patient_ID not in Pateints_DataBase :
													patient_ID = int(input("Incorrect ID, please Enter a correct patient ID : "))	
										
										# Option to create a new patient while booking.
										elif Admin_choice == "2" :
											patient_ID = int(input("Enter patient ID : "))
											while patient_ID in Pateints_DataBase :
												patient_ID = int(input("This ID is unavailable, please try another ID : "))					
											Department=Doctors_DataBase[Doctor_ID][0][0]
											DoctorName=Doctors_DataBase[Doctor_ID][0][1]
											Name      =input("Enter patient name    : ")
											Age       =input("Enter patient age     : ")
											Gender    =input("Enter patient gender  : ")
											Address   =input("Enter patient address : ")
											RoomNumber="" # No room number for outpatients.
											Pateints_DataBase[patient_ID]=[Department,DoctorName,Name,Age,Gender,Address,RoomNumber]
										
										elif Admin_choice == "B" :
											break
											
										Session_Start = input("Session starts at : ")
										# This logic checks for specific invalid morning hours.
										while Session_Start[ :2] == "11" or Session_Start[ :2] == "12" :
											Session_Start = input("Appointments should be between 01:00PM to 10:00PM, Please enter a time between working hours : ")
											
										# Check for appointment conflicts.
										for i in Doctors_DataBase[Doctor_ID] :
											if type(i[0])!=str :
												while Session_Start >= i[1] and Session_Start < i[2] :
													Session_Start = input("This appointment is already booked, Please Enter an other time for start of session : ")
										Session_End   = input("Session ends at : ")
										
										New_Appointment=list()
										New_Appointment.append(patient_ID)
										New_Appointment.append(Session_Start)
										New_Appointment.append(Session_End)
										# Add the new appointment to the doctor's list.
										Doctors_DataBase[Doctor_ID].append(New_Appointment)								
										print("/----------------------Appointment booked successfully----------------------/")
								except :
										print("Doctor ID should be an integer number")
					
							# --- 3.2: Edit an Appointment ---
							elif Admin_choice == "2" :
									try :
										patient_ID = int(input("Enter patient ID : "))						
										while patient_ID not in Pateints_DataBase :
											patient_ID = int(input("Incorrect Id, Please Enter correct patient ID : "))
										# A nested try-except to handle cases where the appointment doesn't exist.
										try :
												# Find the appointment's location first.
												AppointmentIndex,PairKey = AppointmentIndexInDoctorsDataBase(patient_ID)
												Session_Start = input ("Please enter the new start time : ")
												while Session_Start[ :2] == "11" or Session_Start[ :2] == "12" :
													Session_Start = input("Appointments should be between 01:00PM to 10:00PM, Please enter a time between working hours : ")
													
												# Check for conflicts with the new time.
												for i in Doctors_DataBase[Doctor_ID] :
													if type(i[0])!=str :
														while Session_Start >= i[1] and Session_Start < i[2] :
															Session_Start = input("This appointment is already booked, Please Enter an other time for start of session : ")
												Session_End = input ("Please enter the new end time : ")
												# Update the appointment in place.
												Doctors_DataBase[PairKey][AppointmentIndex]=[patient_ID,Session_Start,Session_End]							
												print("/----------------------appointment edited successfully----------------------/")
										except :
												print("No Appointment for this patient")
									except :
										print("Doctor ID should be an integer number")
						
							# --- 3.3: Cancel an Appointment ---
							elif Admin_choice == "3" :
									try :
										patient_ID = int(input("Enter patient ID : "))
										while patient_ID not in Pateints_DataBase :
											patient_ID = int(input("Invorrect ID, Enter patient ID : "))
										try :
												AppointmentIndex,PairKey = AppointmentIndexInDoctorsDataBase(patient_ID)						
												# Remove the appointment from the doctor's list.
												Doctors_DataBase[PairKey].pop(AppointmentIndex)
												print("/----------------------appointment canceled successfully----------------------/")
										except :
												print("No Appointment for this patient")
									except :
										print("Patient ID should be an integer number")
							
							# --- 3.4: Back ---
							elif Admin_choice == "B" :
										break
							
							else :
										print("please enter a correct choice")
						
						# --- Admin Menu: Back ---
						elif AdminOptions == "B" :
							break
						
						else :
							print("Please enter a correct option")
					
				
					# --- Incorrect Password Handling ---
					elif Password != "1234" :
						if tries < 2 :
							Password = input("Password incorrect, please try again : ")
							tries += 1
						else :
							print("Incorrect password, no more tries")
							# This flag will cause the main program loop to terminate.
							tries_flag = "Close the program"
							break
				
					# --- Save Changes to Files ---
					# After any potential modification in the admin loop, write the updated data back to the CSVs.
					Write_Hospital_Excel_Sheet.Write_Patients_DataBase(Pateints_DataBase)
					Write_Hospital_Excel_Sheet.Write_Doctors_DataBase(Doctors_DataBase)
					
					
		# =================================================================================
		# --- User Mode ---
		# =================================================================================
		elif Admin_user_mode == "2" :
			print("****************************************\n|         Welcome to user mode         |\n****************************************")
			# This loop handles all actions within the User Mode.
			while True :
				print("\n-----------------------------------------")
				print("|To view hospital's departments Enter 1 |")
				print("|To view hospital's docotrs Enter 2     |")
				print("|To view patients' residents Enter 3    |")
				print("|To view patient's details Enter 4      |")
				print("|To view doctor's appointments Enter 5  |")
				print("|To be Back Enter B                     |")
				print("-----------------------------------------")
				UserOptions = input("Enter your choice : ")
				UserOptions = UserOptions.upper()
				
				# --- 5.1: View Hospital Departments ---
				if   UserOptions == "1" :
							print("Hospital's departments :")
							# This loop may print duplicate department names.
							for i in Doctors_DataBase :
								print("	"+Doctors_DataBase[i][0][0])
					
				# --- 5.2: View Hospital Doctors ---
				elif UserOptions == "2" :
							print("Hospital's doctors :")
							for i in Doctors_DataBase :
								print("	"+Doctors_DataBase[i][0][1]+" in "+Doctors_DataBase[i][0][0]+" department, from "+Doctors_DataBase[i][0][2])
								
				# --- 5.3: View Patient Residents ---
				elif UserOptions == "3" :
					for i in Pateints_DataBase :
						print("	Patient : "+Pateints_DataBase[i][2]+" in "+Pateints_DataBase[i][0]+" department and followed by "+Pateints_DataBase[i][1]+", age : "+Pateints_DataBase[i][3]+", from : "+Pateints_DataBase[i][5]+", RoomNumber : "+Pateints_DataBase[i][6])
				
				# --- 5.4: View Patient Details by ID ---
				elif UserOptions == "4" :
					try :
						patient_ID = int(input("Enter patient's ID : "))
						while patient_ID not in Pateints_DataBase :
							patient_ID = int(input("Incorrect Id, Please enter patient ID : "))
						print("	patient name        : ",Pateints_DataBase[patient_ID][2])
						print("	patient age         : ",Pateints_DataBase[patient_ID][3])
						print("	patient gender      : ",Pateints_DataBase[patient_ID][4])
						print("	patient address     : ",Pateints_DataBase[patient_ID][5])
						print("	patient room number : ",Pateints_DataBase[patient_ID][6])
						print("	patient is in "+Pateints_DataBase[patient_ID][0]+" department")
						print("	patient is followed by doctor : "+Pateints_DataBase[patient_ID][1])
					except :
						print("Patient ID should be an integer number")
							
				# --- 5.5: View Doctor's Appointments by ID ---
				elif UserOptions == "5" :
					try :
						Doctor_ID = int(input("Enter doctor's ID : "))
						while Doctor_ID not in Doctors_DataBase :
							Doctor_ID = int(input("Incorrect Id, Please enter doctor ID : "))
						print(Doctors_DataBase[Doctor_ID][0][1]+" has appointments :")
						for i in Doctors_DataBase[Doctor_ID] :
							# Skip the first item, which is the doctor's details.
							if type(i[0])==str :
								continue
							else :
								print("	from : "+i[1]+"    to : "+i[2])
					except :
						print("Doctor ID should be an integer number")
					
				# --- 5.6: Back ---
				elif UserOptions == "B" :
					# Break from the user mode loop to return to the main mode selection.
					break
					
				else :
					print("Please Enter a correct choice")
					
		# --- Invalid Mode Selection ---
		else :
			print("Please choice just 1 or 2")

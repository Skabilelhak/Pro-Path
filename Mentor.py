
import pandas as pd
from PIL import Image
from Core import Apprenant,Mentor
import base64




def mentor_page(username):
    def Mentor_list(email):
        lignes = pd.read_csv('Mentor1.csv', sep=',')
        elements = []
        for i in range(len(lignes)):
            if lignes.loc[i][2] == email:
                elements = [lignes.loc[i]['username'], lignes.loc[i]['first_name'], lignes.loc[i]['email'], lignes.loc[i]['password']]
        return elements

    elements = Mentor_list(username)

    def Afficher_demande(elements):
        A = Mentor(elements[0], elements[1], elements[2], elements[3])
        demandes_mentor = A.afficher_demandes_pour_mentor()
        
        # Converting demandes_mentor to a list of dictionaries
        demandes_mentor_df = pd.DataFrame(demandes_mentor, columns=["First_name", "username", "Email", "Subject", "date", "time"])
        demandes_mentor_list = demandes_mentor_df.to_dict(orient="records")
        
        return demandes_mentor_list
    
    # Return the formatted data for the table
    return Afficher_demande(elements)

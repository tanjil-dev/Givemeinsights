import pandas as pd
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Person
from .serializers import PersonSerializer

class PersonListView(APIView):
    #Get all the data from Person table entries
    def get(self, request):
        people = Person.objects.all()
        serializer = PersonSerializer(people, many=True)
        return Response(serializer.data)
    #Delete all the data from Person table entries
    def delete(self, request):
        Person.objects.all().delete()
        return Response({'message': 'All data deleted successfully!'}, status=status.HTTP_204_NO_CONTENT)

#gets data from frontend form and save those data into the Person table    
class UploadExcelView(APIView):
    def post(self, request):
        if 'file' not in request.FILES:
            return Response({'error': 'No file uploaded'}, status=400)
        
        try:
            excel_file = request.FILES['file']
            df = pd.read_excel(excel_file, engine='openpyxl')
            expected_columns = ['name', 'address']

            #Throw error for invalid excel file structure
            if not all(column in df.columns for column in expected_columns):
                return Response({'error': 'Invalid file structure. Expected columns: name, address'}, status=400)
            
            #Loop for inserting rows from excel file
            for index, row in df.iterrows():
                Person.objects.create(name=row['name'], address=row['address'])
            
            return Response({'message': 'Data uploaded successfully'}, status=200)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
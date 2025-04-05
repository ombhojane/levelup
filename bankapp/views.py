from django.http import HttpResponse
import csv
import os

def get_csv_data(request):
    """
    Handles the request to fetch data from prodtest.csv.
    The request parameter is required by Django views, even if not explicitly used.
    """
    csv_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'branches', 'script', 'prodtest.csv'
    )

    try:
        with open(csv_file_path, mode='r') as file:
            response = HttpResponse(file.read(), content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="prodtest.csv"'
            return response
    except FileNotFoundError:
        return HttpResponse("Error: CSV file not found.", status=404)

from cornice import Service

from powerwall.extract import BaseExtractor

ex_data = Service(name='extractor', path='/rest/extract/{name}/data', description='Getting data from extractors')


@ex_data.get()
def get_extractor_data(request):
    """Get the data from an exractor in CSV format"""

    # Get the requested extractor
    name = request.matchdict['name']

    try:
        ex = BaseExtractor.objects.get(name=name)

        # Return in desired format
        return {"data": ex.get_data().to_csv(index=False)}
    except:
        return "Nothing found"

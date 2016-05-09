import datetime
import time
import json

DATE_FORMAT = "%d/%m/%y %H:%M" 

def time_to_time_string(time):
     dt = datetime.datetime.fromtimestamp(time)
     return  dt.strftime(DATE_FORMAT)

BASIC_ANIMAL_FORMAT = """Animal
------
Name: {0}
Gender: {1}
Location: {2}, {3}
ID: {4}"""

TRACKER_ANIMAL_FORMAT = """Animal
------
Name: {0}
Gender: {1}
Location: {2}, {3}
Time: {4}
ID: {5}
Tracker ID: {6}"""


PLANT_FORMAT = """Plant
-----
Name: {0}
Location: {1}, {2}
ID: {3}"""

def load_model(filename):
    """Return a model built from the data in the supplied json file

    load_model(str) -> SurveyModel
    """
    with open(filename, 'r') as f:
        text = f.read()

    model_info = json.loads(text)
    model = SurveyModel()
    model.set_name(model_info['name'])
    model.set_image_file(model_info['image'])
    model.set_organisms(model_info['organisms'])
    model.set_trackers(model_info['trackers'])
    return (model)


def save_model(model, filename):
    """Write the data in model to the supplied file

    save_model(SurveyModel, str) -> None
    """
    with open(filename, 'w') as f:
        d = {'name': model.get_name(),
             'image': model.get_image_file(),
             'organisms': model.get_organism_dictionary(),
             'trackers': model.get_tracker_dictionary()
        }
        f.write(json.dumps(d, sort_keys=True,
                           indent=4, separators=(',', ': ')))

def run_GUI():
    """
    Runs the Survey GUI using this script's classes for the models.

    run_GUI() -> None
    """
    import survey

    items = list(globals().items())
    for key, value in items:
        survey.__dict__['model2'].__dict__[key] = value

    root = survey.tk.Tk()
    app = survey.SurveyApp(root)
    root.mainloop()
    
## End of support code
################################################################
# Write your code below
################################################################

class TrackerError(Exception):
    """
    Error for an invalid tracker id.
    """
    def __init__(self, tid):
        """
        Constructor

        TrackerError.__init__(str)
        """
        super().__init__(tid)

class SurveyModel(object):
    """
    The top-level model class for a survey.
    """
    def __init__(self):
        """
        Constructor

        SurveyModel.__init__()
        """
        self.name = None
        self.imagefile = None
        self.organisms = {}
        self.trackers = {}

    def get_organism_dictionary(self):
        """
        Returns a dictionary whose keys are the keys in the organism dictionary and whose values are the organism objects converted to a dictionary.

        SurveyModel.get_organism_dictionary() -> {str: dict}
        """
        d = {}
        for key in self.organisms:
            d[key] = self.organisms[key].to_dictionary()
        return d

    def get_tracker_dictionary(self):
        """
        Returns the tracker dictionary (for saving).

        SurveyModel.get_tracker_dictionary() -> {str: str}
        """
        return self.trackers

    def set_trackers(self, d):
        """
        Load up the trackers dictionary with the supplied dictionary loaded from a json file.

        SurveyModel.set_trackers(dict) -> None
        """
        self.trackers = d

    def set_organisms(self, d):
        """
        Load up the organisms dictionary with the supplied dictionary loaded from a json file.

        SurveyModel.set_organism(dict) -> None
        """
        self.organisms = {}
        for key in d:
            od = d[key]
            if od['type'] == 'animal':
               animal = Animal(od['position'], od['name'],
                               od['gender'], od['tracker_id'])
               animal.set_id(od['id'])
               self.organisms[key] = animal
            else:
               plant = Plant(od['position'], od['name'])
               plant.set_id(od['id'])
               self.organisms[key] = plant
        
    def set_name(self, name):
        """
        Sets the name of the survey.

        SurveyModel.set_name(str) -> None
        """
        self.name = name

    def get_name(self):
        """
        Returns the name of the survey.

        SurveyModel.get_name() -> str
        """
        return self.name

    def set_image_file(self, filename):
        """
        Sets the filename of the image of the model

        SurveyModel.set_image_file(str) -> None
        """
        self.imagefile = filename

    def get_image_file(self):
        """
        Returns the filename of the image of the model

        SurveyModel.get_image_file() -> str
        """
        return self.imagefile

    def add_tracker(self, tracker_id, animal):
        """
        Add an entry to the tracker dictionary whose key is tracker_id and whose value is the ID of animal.
        Raises a TrackerError(tracker_id) exception if tracker_id is already a key in the tracker dictionary.

        SurveyModel.add_tracker(str, Animal) -> None
        """
        if tracker_id in self.trackers:
            raise TrackerError("Tracker id {} is already in use!".format(tracker_id))

        self.trackers[tracker_id] = animal.get_id()

    def add_organism(self, organism):
        """
        Add an entry to the organism dictionary whose key is the ID of organism and whose value is organism.

        SurveyModel.add_organism(Organism) -> None
        """
        self.organisms[organism.get_id()] = organism

    def get_organism_ids(self):
        """
        Returns the list of organism IDs (i.e. keys of the organism dictionary).

        SurveyModel.get_organism_ids() -> [str]
        """
        return self.organisms.keys()

    def get_organism(self, tracker_id):
        """
        Returns the organism with the given ID from the organism dictionary.

        SurveyModel.get_organism(str) -> Organism
        """
        return self.organisms[tracker_id]

    def update_location(self, tracker_id, position):
        """
        Add position together with the current time (by calling time.time()) to the animal with ID organism_id.
        Position is an integer pair of xy-coordinates.
        Raises a TrackerError(tracker_id) exception if tracker_id is not a key in the tracker dictionary.

        SurveyModel.update_location(str, [int, int]) -> None
        SurveyModel.update_location(str, [[[int, int], float], ...]) -> None
        """
        try:
            animal = self.organisms[self.trackers[tracker_id]]
            animal.add_location(position)
        except KeyError:
            raise TrackerError(tracker_id)

class Organism(object):
    """
    Base class for any organism that can be plotted in the survey.
    """

    count = 1

    def __init__(self, position, name):
        """
        Constructor

        Organism.__init__([int, int], str)
        """
        self.position = position
        self.id = "id_{0}".format(self.count)
        Organism.count += 1
        self.name = name

    def get_id(self):
        """
        Returns the ID of the object.

        Organism.get_id() -> str
        """
        return self.id

    def set_id(self, id):
        """
        Sets the ID of the object.

        Organism.set_id(str) -> None
        """
        self.id = id

    def get_position(self):
        """
        Returns the position of the object.

        Organism.get_position() -> [int, int]
        """
        return self.position

    def get_full_position(self):
        """
        Returns the position of the object - intended to be overridden in the Animal class.

        Organism.get_full_position() -> [int, int]
        """
        return self.position

    def get_track(self):
        """
        Returns an empty list - intended to be overridden in the Animal class.

        Organism.get_track() -> []
        """
        return []

    def get_name(self):
        """
        Returns the name of the Organism

        Organism.get_name() -> str
        """
        return self.name

    def to_dictionary(self):
        """
        Returns a dictionary of the information contained in the object - extended in the Plant and Animal class. This dictionary has the form:
        {'name': object_name, 'id': object_id,  'position': full_position}

        Organism.to_dictionary_() -> dict
        """
        return {'name':self.get_name(), 'id':self.get_id(), 
                'position':self.get_full_position()}


class Plant(Organism):
    """
    A plant that can be plotted in the survey.
    """
    def __init__(self, position, name):
        """
        Constructor

        Plant.__init__([int, int], str)
        """
        super().__init__(position, name)

    def __repr__(self):
        """
        Returns a simple text representation of this Plant.

        Plant.__repr__() -> str
        """
        return "{0} {1} {2}".format(self.name, self.position, self.get_id())

    def __str__(self):
        """
        Returns a nicely formatted representation of this Plant.

        Plant.__str__() -> str
        """
        x,y = self.get_position()
        return PLANT_FORMAT.\
            format(self.name, x, y, self.get_id())

    def to_dictionary(self):
        """
        Return a dictionary of the information contained in the object - extends the Organism dictionary with {'type': 'plant'}.

        Plant.to_dictionary() -> dict
        """
        d = super().to_dictionary()
        d['type'] = 'plant'
        return d



class Animal(Organism):
    """
    A animal that can be plotted in the survey.
    """
    def __init__(self, position, name, gender, tracker_id):
        """
        Constructor

        Animal.__init__([[[int, int], float], ...], str, str, str)
        """
        super().__init__(position, name)
        self.name = name
        self.gender = gender
        self.tracker_id = tracker_id

    def get_position(self):
        """
        Returns the xy-coordinates of the Animal's current position (i.e. the last entry in the position list).

        Animal.get_position() -> [int, int]
        """
        return self.position[-1][0]

    def add_location(self, position):
        """
        Adds the position together with the current time to the position list.

        Animal.add_location([int, int]) -> None
        """
        self.position.append([position, time.time()])

    def __repr__(self):
        """
        Returns a simple text representation of this Animal.

        Animal.__repr__() -> str
        """
        return "{0}  {1} {2} {3}".format(self.name, self.gender, self.position, self.get_id())
        
    def __str__(self):
        """
        Returns a simple text representation of this Animal.

        Animal.__repr__() -> str
        """
        x, y = self.get_position()
        if self.tracker_id:
            time = self.position[-1][1]
            return TRACKER_ANIMAL_FORMAT.format(self.name, self.gender, x, y,
                                                time_to_time_string(time), 
                                                self.get_id(), self.tracker_id)
        else:
            return BASIC_ANIMAL_FORMAT.format(self.name, self.gender, 
                                              x, y, self.get_id())

    def get_track(self):
        """
        Returns [] if there is only one entry in the position list, otherwise it returns the list of xy-coordinate pairs in the position list.

        Animal.get_track() -> [[int, int], ...]
        """
        track = self.position
        if len(track) == 1:
            return []
        else:
            return [pos for pos, _ in track]
        
    def to_dictionary(self):
        """
        Return a dictionary of the information contained in the object - extends the Organism dictionary with {'type': 'animal', 'tracker_id': tracker_id, 'gender': gender} where tracker_id is the tracker ID and gender is either 'male' or 'female'.

        Animal.to_dictionary() -> dict
        """
        d = super().to_dictionary()
        d['gender'] = self.gender
        d['tracker_id'] = self.tracker_id
        d['type'] = 'animal'
        return d


################################################################
# Write your code above
################################################################

## Uncomment the following code to automatically run the GUI
# if __name__ == '__main__':
#     run_GUI()

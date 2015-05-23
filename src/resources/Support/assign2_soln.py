from assign2_support import *

class TemperatureData(object):
    def __init__(self):
        self._data = {}
        self._stations = []
        self._selected = []

    def load_data(self, stationfile):
        station = Station(stationfile)
        station_name = station.get_name()
        if station_name in self._stations:
            return
        self._data[station_name] = Station(stationfile)
        self._stations.append(station_name)
        self._selected.append(True)
        self.reset_minmax()

    def is_selected(self, i):
        return self._selected[i]

    def toggle_selected(self, i):
        self._selected[i] = not self._selected[i]

    def get_data(self):
        return self._data

    def get_stations(self):
        return self._stations

    def reset_minmax(self):
        self._min_year = 10000
        self._max_year = 0
        self._min_temp = 500
        self._max_temp = -100
        for key in self._data:
            min_year, max_year = self._data[key].get_year_range()
            min_temp, max_temp = self._data[key].get_temp_range()
            self._min_year = min(min_year, self._min_year)
            self._max_year = max(max_year, self._max_year)
            self._min_temp = min(min_temp, self._min_temp)
            self._max_temp = max(max_temp, self._max_temp)
    
    def get_ranges(self):
        return (self._min_year, self._max_year, self._min_temp, self._max_temp)
            
class SelectionFrame(tk.Frame):
    def __init__(self, parent, data, plotter):
        super().__init__(parent)
        self._data = data
        self._plotter = plotter
        tk.Label(self, text="Station Selection:  ").pack(side=tk.LEFT)
    
    def refresh(self):
        stations = self._data.get_stations()
        if stations == []:
            return
        i = len(stations)-1
        s = stations[-1]
        cb = tk.Checkbutton(self, text=s, fg=COLOURS[i], 
                       command=self.press(i))
        cb.pack(side=tk.LEFT)
        cb.select()

    def press(self, i):
        return lambda : self.press_i(i)

    def press_i(self, i):
        self._data.toggle_selected(i)
        self._plotter.redraw()
        
class DataFrame(tk.Frame):
    def __init__(self, parent, data):
        super().__init__(parent)
        self._data = data
        self._top_label = tk.Label(self, text="")
        self._top_label.pack(side=tk.LEFT, pady=10)
        self._labels = []

    def clear_label_text(self):
        for label in self._labels:
            label.config(text="            ")
        self._top_label.config(text="")

    def show_data(self, year):
        data = self._data.get_data()
        for _ in range(len(data) - len(self._labels)):
            label = tk.Label(self, text="")
            label.pack(side=tk.LEFT, pady=10)
            self._labels.append(label)
        self._top_label.config(text="Data for {0}:".format(year))
        for i, s in enumerate(self._data.get_stations()):
            if self._data.is_selected(i):
                temps = data[s]
                temp = temps.get_temp(year)
                if temp is not None:
                    self._labels[i].config(text="{0:12.3f}".format(temp), 
                                           fg = COLOURS[i])

class Plotter(tk.Canvas):

    def __init__(self, parent, data, data_frame):
        self._width = 0
        self._height = 0
        super().__init__(parent, bg='white',
                        width=self._width, height=self._height,
                        relief=tk.SUNKEN, bd=2)
        self._data = data
        self._data_frame = data_frame
        self._ws = None
        self.bind("<Configure>", self._resize)
        self.bind("<Button-1>", self._click)
        self.bind("<Button-2>", self._click_2)
        self.bind("<B1-Motion>", self._show_data)
        # CSSE7030
        self.bind_all("<Key>", self._key)
        self._start_year = None
        self._end_year = None
        self.line = None
        self._clicked_year = None

    
    def _click(self, e):
        if self._ws is None:
            return
        self._clicked_year = self._ws.get_year(e.x)
        self.redraw()

    def _click_2(self, e):
        self._clicked_year = None
        self.redraw()

    def _key(self, _e): 
        if self._start_year is None or self._end_year is not None:
            self._end_year = None
            self._start_year = self._clicked_year
        else:
            self._end_year =  self._clicked_year
        self.redraw()
            
    def _show_data(self, e):
        if not 0 <= e.x < self._width:
            return
        self._clicked_year = self._ws.get_year(e.x)
        self.redraw()

    def _resize(self, e):
        """Callback for a resize event - reset the canvas size."""
        self._width, self._height = e.width, e.height
        if self._ws is None:
            return
        self._ws.resize(self._width, self._height)
        self.redraw()
          
    def refresh(self):
        data = self._data.get_data()
        if not data:
            return
        miny, maxy, mint, maxt = self._data.get_ranges()
        self._ws = CoordinateTranslator(self._width, self._height,
                                        miny, maxy, mint, maxt)
        self.redraw()

    def redraw(self):
        self.delete(tk.ALL)
        self._data_frame.clear_label_text()
        stations = self._data.get_stations()
        data = self._data.get_data()
        if not data:
            return
        colour_index = 0
        for i, key in enumerate(stations):
            if self._data.is_selected(i):
                points = [self._ws.temperature_coords(year, temp) \
                          for year, temp in data[key].get_data_points()]
                self.create_line(points, fill=COLOURS[colour_index])
                if self._end_year is not None:
                    self.draw_line_fit(data[key].get_data_points(), 
                                       COLOURS[colour_index])
            colour_index += 1
        if self._clicked_year is not None:
            x, _ = self._ws.temperature_coords(self._clicked_year, 0)
            self.line = self.create_line(x, 0, x, self._height)
            self._data_frame.show_data(self._clicked_year)
     
    # CSSE7030
    def draw_line_fit(self, data, colour):
        if self._start_year < self._end_year:
            start, end = self._start_year, self._end_year
        else:
            end, start = self._start_year, self._end_year
        points = [self._ws.temperature_coords(year, temp) \
                  for year, temp in data if \
                  start <= year <= end]
        (start, end) = best_fit(points)
        self.create_line([start, end], fill=colour, width=2)
        

class TemperaturePlotApp(object):
    """The controller class"""

    def __init__(self, master):
        master.title("Max Temperature Plotter")
        self._temp_data = TemperatureData()
        self._dataframe = DataFrame(master, self._temp_data)
        self._plotter = Plotter(master, self._temp_data, 
                                self._dataframe)
        self._plotter.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self._dataframe.pack(side=tk.TOP, fill=tk.X) 
        self._options = SelectionFrame(master, self._temp_data, self._plotter)
        self._options.pack(side=tk.TOP, fill=tk.X)
        menubar = tk.Menu(master)
        master.config(menu=menubar)
        filemenu = tk.Menu(menubar)
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Open", command=self.open_file)
        
    def open_file(self):
        filename = filedialog.askopenfilename()
        if filename:
            try:
                self._temp_data.load_data(filename)
                self._plotter.refresh()
                self._options.refresh()
            except:
                messagebox.showerror("File Error", 
                                     "{0} is not a suitable data file".format(stationfile))

        


######################################################################


def main():
    root = tk.Tk()
    app = TemperaturePlotApp(root)
    root.geometry("800x400")
    root.mainloop()

if __name__ == '__main__':
    main()

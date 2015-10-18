#!/usr/bin/env python3

from assign2_support import *

#CSSE7030
from statistics import mean, pstdev

class AnimalData(object):
    """
        A class to handle the management of animal height and weight data.
        Will store the different classes of animal and whether they are
        to be selected for plotting.
    """
    def __init__(self):
        """
            Create an instance of AnimalData to manage the different animal
            data sets.

            Constructor: AnimalData()
        """
        self._sets = {}
        self._selected = []
        self._classes = []
        self._min_height = None
        self._max_height = None
        self._min_weight = None
        self._max_weight = None
       	
    def load_data(self, datafile):
        """
            Loads a new animal data file; adding a DataClass instance to the
            collection of data.

            load_animal_data(str) -> None
        """
        new_data = AnimalDataSet(datafile)
        if self._sets.get(new_data.get_name(), None) is None:
            self._sets[new_data.get_name()] = new_data
            self._selected.append(True)
            self._classes.append(new_data.get_name())

    def is_selected(self, i):
        return self._selected[i]

    def select(self, i):
        self._selected[i] = True

    def deselect(self, i):
        self._selected[i] = False

    def get_ranges(self):
        heights = []
        weights = []
        for i, animal in enumerate(self._classes):
            if self._selected[i]:
                heights.append(self._sets[animal].get_height_range()[0])
                heights.append(self._sets[animal].get_height_range()[1])
                weights.append(self._sets[animal].get_weight_range()[0])
                weights.append(self._sets[animal].get_weight_range()[1])
        if len(heights):
            return (min(heights), max(heights), min(weights), max(weights))
        else:
            return (None, None, None, None)

    def get_animal(self, name) -> AnimalDataSet:
        return self._sets[name]

    def get_animal_names(self):
        return self._classes

    def to_tabbed_string(self, index):
        """
        A prettified string for displaying in the listbox

        to_tabbed_string(int) -> string
        """
        animal = self._sets[self._classes[index]]
        return LABEL_FORMAT.format(animal.get_name(),\
                len(animal.get_data_points()), "Visible" if\
                self._selected[index] else "Hidden")

    def number_selected(self):
        return len([x for x in self._selected if x])

class Plotter(tk.Canvas):
    def __init__(self, parent, animal_data, plot_app):
        self._width = 0
        self._height = 0
        self._data = animal_data
        self._ct = None
        self._parent = plot_app
        super().__init__(parent, bg = 'white',
                        width = self._width, height = self._height,
                        relief = tk.SUNKEN, bd = 2)

        self.bind("<Configure>", self._resize)
        self.bind("<Motion>", self._identify_point)
        self.bind("<Leave>", self._mouse_exit)
        self._highlight = None
        self.refresh()

    def draw_points(self):
        for i, name in enumerate(self._data.get_animal_names()):
            if self._data.is_selected(i):
                points = [self._ct.get_coords(x, y) for x, y in \
                        self._data.get_animal(name).get_data_points()]
                for x, y in points:
                    self.create_rectangle(x - 2, y - 2, x + 2, y + 2, fill = \
                            COLOURS[i % len(COLOURS)], outline = COLOURS[i %\
                            len(COLOURS)])

    def redraw(self):
        self.delete(tk.ALL)
        self.draw_points()

    def refresh(self):
        if self._data.number_selected():
            minx, maxx, miny, maxy = self._data.get_ranges()
            self._ct = CoordinateTranslator(self.winfo_width(),\
                    self.winfo_height(), minx, maxx, miny, maxy)
        self.redraw()

    def _resize(self, e):
        self._width = e.width
        self._height = e.height
        if self._ct is not None:
            self._ct.resize(self._width, self._height)
        self.redraw()

    def _identify_point(self, e):
        if self._data.number_selected():
            if self._highlight is not None:
                self.delete(self._highlight[0])
                self.delete(self._highlight[1])
            horiz = self.create_line(0, e.y, self._width, e.y)
            vert = self.create_line(e.x, 0, e.x, self._height)
            self._highlight = (horiz, vert)
            self._parent.update_plot_stats(self._ct.get_height(e.x),\
                    self._ct.get_weight(e.y))

    def _mouse_exit(self, e):
        if self._highlight is not None:
            self.delete(self._highlight[0])
            self.delete(self._highlight[1])
            self._highlight = None

class SelectionBox(tk.Listbox):
    def __init__(self, parent, plotter, animal_data, font_obj):
        self._animal_data = animal_data
        self._plotter = plotter
        super().__init__(parent, bg = "white", width = 30, relief = tk.SUNKEN,\
                bd = 2, font = font_obj)

    def update(self):
        self.delete(0, tk.END)
        for i, animal in enumerate(self._animal_data.get_animal_names()):
            self.insert(tk.END, self._animal_data.to_tabbed_string(i))
            self.itemconfigure(i, foreground = COLOURS[i % len(COLOURS)])


class SummaryWindow(tk.Toplevel):
    def __init__(self, selection_box: SelectionBox, data: AnimalData):
        super().__init__()
        self._selection_box = selection_box
        self._data = data
        self._selection_box.bind()
        self.wm_title("Animal Summary")

        labels = []
        labels.append(tk.Label(self, text="Animal: "))
        labels.append(tk.Label(self, text="Data points: "))
        labels.append(tk.Label(self, text="Weight Mean: "))
        labels.append(tk.Label(self, text="Height Mean: "))
        labels.append(tk.Label(self, text="Weight Variance: "))
        labels.append(tk.Label(self, text="Height Variance: "))

        self._labels = labels

        for label in labels:
            label.pack(side=tk.TOP)

        self.update()

        self._selection_box.bind("<<ListboxSelect>>", lambda x: self.update())

    def update(self):
        animal_idx = self._selection_box.curselection()[0]
        animal_name = self._data.get_animal_names()[animal_idx]
        self._labels[0].config(text="Animal: "+animal_name)

        data = self._data.get_animal(animal_name).get_data_points()
        weights = [y for x,y in data]
        heights = [x for x,y in data]
        """Alternatively:
        weights = []
        heights = []
        for w,h in data:
            weights.append(w)
            heights.append(h)
        """
        count = len(data)
        w_mean = mean(weights)
        h_mean = mean(heights)
        w_var = pstdev(weights)
        h_var = pstdev(heights)

        self._labels[1].config(text=self._format_label("Data points:",count))
        self._labels[2].config(text=self._format_label("Weight mean:",w_mean))
        self._labels[3].config(text=self._format_label("Height mean:",h_mean))
        self._labels[4].config(text=self._format_label("Weight std dev:", w_var))
        self._labels[5].config(text=self._format_label("Height std dev:", h_var))

    def _format_label(self, arg1, arg2):
        result = arg1.rjust(15," ")
        if isinstance(arg2,float):
            arg2 = round(arg2,2)
        arg2 = str(arg2)
        result += arg2.rjust(15, " ")
        return result


class AnimalDataPlotApp(object):
    def __init__(self, master):
        master.title("Animal Data Plot App")
        self._animal_data = AnimalData()
        plot_frame = tk.Frame(master)
        self._plotter = Plotter(plot_frame, self._animal_data, self)
        selection_frame = tk.Frame(master)
        self._selector = SelectionBox(selection_frame, self._plotter,\
                self._animal_data, SELECTION_FONT)
        tk.Label(selection_frame, text = "Animal Data Sets").pack(side = tk.TOP)

        self._cursor_stat = tk.Label(plot_frame)
        set_select_frm = tk.Frame(selection_frame)
        self._select_btn = tk.Button(set_select_frm, text = "Select  ",\
                command = self._select)
        self._select_btn.pack(side = tk.LEFT, expand = True, fill = tk.X)
        self._deselect_btn = tk.Button(set_select_frm, text = "Deselect",
                command = self._deselect)
        self._deselect_btn.pack(side = tk.LEFT, expand = True, fill = tk.X)
        set_select_frm.pack(side = tk.TOP, fill = tk.X)

        self._selector.pack(side = tk.TOP, fill = tk.BOTH, expand = True)
        selection_frame.pack(side = tk.LEFT, fill = tk.BOTH)
        self._cursor_stat.pack(side = tk.TOP)
        self._plotter.pack(side = tk.LEFT, expand = True, fill = tk.BOTH)
        plot_frame.pack(side = tk.LEFT, expand = True, fill = tk.BOTH)

        menubar = tk.Menu(master)
        master.config(menu=menubar)
        filemenu = tk.Menu(menubar)
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Open", command=self.open_file)

        #CSSE7030
        self._window = None
        self._summary_btn = tk.Button(set_select_frm, text="Summary", command = self._show_summary)
        self._summary_btn.pack(side = tk.LEFT, expand = True, fill = tk.X)
        
    def open_file(self):
        filename = filedialog.askopenfilename()
        if filename:
            try:
                self._animal_data.load_data(filename)
                self._plotter.refresh()
                self._selector.update()
            except FileExtensionException as e:
                messagebox.showerror("File Error",\
                        "{0} has an invalid file extension".format(filename))
            except (ValueError, IndexError) as e:
                messagebox.showerror("File Error",\
                        "{0} is an invalid Animal Data file".format(filename))
            except FileNotFoundError as e:
                messagebox.showerror("File Error",\
                        "File: {0} not found".format(filename))

    def update_plot_stats(self, h, w):   
        self._cursor_stat.config(text = "Height: {0} cm, Weight: {1} kg".\
                format(round(h, 2), round(w, 2)))


    #CSSE7030
    def _show_summary(self):
        if self._selector.curselection() and not self._window:
            self._window = SummaryWindow(self._selector,self._animal_data)
            self._window.bind("<Destroy>", self._clear_summary)
        self._window.protocol("WM_DELETE_WINDOW", self._clear_summary)

    #CSSE7030
    def _clear_summary(self, *args):
        self._window.destroy()
        self._window = None
        self._selector.config(command = None)

    def _select(self):
        try:
            item = int(self._selector.curselection()[0])
            self._animal_data.select(item)
            self._plotter.refresh()
            self._selector.update()
        except IndexError:
            tk.messagebox.showerror("Error", "No data set highlighted")

    def _deselect(self):
        try:
            item = int(self._selector.curselection()[0])
            self._animal_data.deselect(item)
            self._plotter.refresh()
            self._selector.update()
            if not self._animal_data.number_selected():
                self._cursor_stat.config(text = "")
        except IndexError:
            tk.messagebox.showerror("Error", "No data set highlighted")

######################################################################

def main():
    root = tk.Tk()
    app = AnimalDataPlotApp(root)
    root.geometry("800x400")
    root.mainloop()

if __name__ == '__main__':
    main()
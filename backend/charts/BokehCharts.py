import backend.metrics.SystemMetrics as sm
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.themes import Theme
from bokeh.document import Document

class BokehCharts:
    def __init__(self):
        self.system_metrics = sm.SystemMetrics()

    def create_doc(self, title):
        doc = Document(title=title)
        doc.theme = Theme(filename='static/bokeh/theme/theme.json')
        return doc

    def configure_plot(self, plot):
        plot.legend.update(**{ 'location': 'top_left', 'background_fill_color': '#232323', 'label_text_color': '#a8a8a8' })
        plot.toolbar.logo = None
        return plot

    def get_cpu_usage_plot(self, x, y):
        cpu_doc = self.create_doc('cpu_usage')
        p = figure(name='cpu_usage', x_axis_label='Seconds', y_axis_label='%', tools='', x_range=(60, 0),
                    height=900, width=1600, sizing_mode='stretch_both', y_axis_location='right')
        p.line(x, y, legend_label="cpu usage", line_width=2, line_color='#b31b1b')
        p = self.configure_plot(p)
        cpu_doc.add_root(p)
        script, div = components(p)

        return {'script': script, 'div': div}

    def get_mem_usage_plot(self, x, y):
        mem_doc = self.create_doc('mem_usage')
        p = figure(name='mem_usage', x_axis_label='Seconds', y_axis_label='%', tools='', x_range=(60, 0),
                    y_range=(0, 100), height=900, width=1600, sizing_mode='stretch_both', y_axis_location='right')
        p.line(x, y, legend_label="memory usage", line_width=2, line_color='#b31b1b')
        p = self.configure_plot(p)
        mem_doc.add_root(p)
        script, div = components(p)

        return {'script': script, 'div': div}

    def get_charts(self):
        figure_models = {}
        x = [i for i in range(self.system_metrics.buffer_len)][::-1]
        figure_models['cpu_usage'] = self.get_cpu_usage_plot(x, list(self.system_metrics.cpu_chart_buffer))
        figure_models['mem_usage'] = self.get_mem_usage_plot(x, list(self.system_metrics.mem_chart_buffer))

        return figure_models

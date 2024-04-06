import metrics.SystemMetrics as sm
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, CustomJS
from bokeh.themes import Theme

class BokehCharts:
    def __init__(self):
        self.system_metrics = sm.SystemMetrics()

    def get_cpu_chart(self):
        x = [i for i in range(61)][::-1]
        y = list(self.system_metrics.cpu_chart_buffer)

        p = figure(name='cpu_usage', x_axis_label='Seconds', y_axis_label='%', tools='', x_range=(60, 0),
                    height=900, width=1600, sizing_mode='stretch_both', y_axis_location='right')
        p.line(x, y, legend_label="cpu usage", line_width=2, line_color='#b31b1b')
        p.legend.location = 'top_left'
        p.legend.background_fill_color = "#232323"
        p.legend.label_text_color = "#a8a8a8"
        p.toolbar.logo = None
        curdoc().theme = Theme(filename='charts/theme/theme.json')
        curdoc().add_root(p)

        return components(p)

    def get_mem_chart(self):
        x = [i for i in range(61)][::-1]
        y = list(self.system_metrics.mem_chart_buffer)

        p = figure(name='mem_usage', x_axis_label='Seconds', y_axis_label='%', tools='', x_range=(60, 0),
                    y_range=(0, 100), height=900, width=1600, sizing_mode='stretch_both', y_axis_location='right')
        p.line(x, y, legend_label="memory usage", line_width=2, line_color='#b31b1b')
        p.legend.location = 'top_left'
        p.legend.background_fill_color = "#232323"
        p.legend.label_text_color = "#a8a8a8"
        p.toolbar.logo = None
        curdoc().theme = Theme(filename='charts/theme/theme.json')
        curdoc().add_root(p)

        return components(p)

import plotly.plotly as py
from plotly.graph_objs import Scatter3d, Line, Layout, Annotations, Annotation
from plotly.graph_objs import Margin, Scene, XAxis, YAxis, ZAxis, Data, Figure, Font


layt = [(1, 1, 1), (1, 0, 1), (2, 1, 0), (0, 2, 1)]


def draw(node_coords, edges, filename="Test"):
    layt = node_coords
    N = len(layt)

    Xn = [layt[k][0] for k in range(N)]  # x-coordinates of nodes
    Yn = [layt[k][1] for k in range(N)]  # y-coordinates
    Zn = [layt[k][2] for k in range(N)]  # z-coordinates
    Xe = []
    Ye = []
    Ze = []

    for e in edges:
        Xe += [layt[e[0]][0], layt[e[1]][0], None]  # x-coordinates of edge ends
        Ye += [layt[e[0]][1], layt[e[1]][1], None]
        Ze += [layt[e[0]][2], layt[e[1]][2], None]

    trace1 = Scatter3d(x=Xe,
                       y=Ye,
                       z=Ze,
                       mode='lines',
                       line=Line(color='rgb(125,125,125)', width=1),
                       hoverinfo='none'
                       )
    trace2 = Scatter3d(x=Xn,
                       y=Yn,
                       z=Zn,
                       mode='markers',
                       marker=dict(
                            size=3,
                            color='rgba(152, 0, 0, .8)'),
                       hoverinfo='none'
                       )

    axis = dict(showbackground=False,
                showline=False,
                zeroline=False,
                showgrid=False,
                showticklabels=False,
                title=''
                )

    layout = Layout(
        title="The Raiden Network",
        width=1000,
        height=1000,
        showlegend=False,
        scene=Scene(
            xaxis=XAxis(axis),
            yaxis=YAxis(axis),
            zaxis=ZAxis(axis),
        ),
        margin=Margin(
            t=100
        ),
        hovermode='closest',
        annotations=Annotations([
            Annotation(
                showarrow=False,
                text="Data source",
                xref='paper',
                yref='paper',
                x=0,
                y=0.1,
                xanchor='left',
                yanchor='bottom',
                font=Font(
                    size=14
                )
            )
        ]),)

    data = Data([trace1, trace2])
    fig = Figure(data=data, layout=layout)

    py.iplot(fig, filename=filename)

import dataclasses
import json
import pathlib

import npc_lims
import panel as pn
import polars as pl

pn.config.theme = 'dark'
pn.extension('tabulator')

def get_sessions_table() -> pn.widgets.Tabulator:
    """Get sessions for a specific subject and date range."""
    yield pn.indicators.LoadingSpinner(value=True, size=20, name='Fetching data from S3...')
    df = (
        pl.read_parquet('s3://aind-scratch-data/dynamic-routing/status/status.parquet')
        # created by https://github.com/AllenInstitute/npc_lims/actions/workflows/status.yml
        .with_columns(
            # pl.selectors.starts_with('is_').cast(pl.Boolean),
            subject_id=pl.col('session_id').str.split('_').list.get(1),
        )
    )
    def content_fn(row) -> pn.pane.Str:
        info = dataclasses.asdict(npc_lims.get_session_info('_'.join(row['session_id'].split('_')[1:3])))
        print(info)
        return pn.pane.JSON(
            object=json.dumps(info, indent=4, default=str),
            styles={'font-size': '12pt'},
            sizing_mode='stretch_width',
        )
   
    stylesheet = """
    .tabulator-cell {
        font-size: 12px;
    }
    """
    header_filters = {
        'date': {'type': 'input', 'func': 'like', 'placeholder': 'like x'},
        'session_id': {'type': 'input', 'func': 'like', 'placeholder': 'like x'},
    }
    tabulator_editors = {
        'float': {'type': 'number', 'max': 10, 'step': 0.1},
        'bool': {'type': 'tickCross', 'tristate': True, 'indeterminateValue': None},
        'str': {'type': 'list', 'valuesLookup': True},
    }
    table = pn.widgets.Tabulator(
        # hidden_columns=['subject', 'raw asset', 'latest sorted asset'],
        value=df.to_pandas(),
        groupby=['subject_id'],
        selectable=False,
        #disabled=True,
        show_index=False,
        sizing_mode='stretch_width',
        row_content=content_fn,
        embed_content=False,
        stylesheets=[stylesheet],
        formatters= {
            'bool': {'type': 'tickCross'}, # not working        
        },     
        header_filters=header_filters,
        editors=tabulator_editors,
        # buttons={
        #     'trigger': '<button type="button">Sort</button>',
        # }
    )
    # def callback(event):
    #     if event.column == 'trigger':
    #         try_run_sorting(df['session'].iloc[event.row])
        ## expand row
        # else:
        #     table.expanded = [event.row] if event.row not in table.expanded else []
        #     table._update_children()
    # table.on_click(callback)
    yield table

    
bound_get_session_df = pn.bind(get_sessions_table)
pn.template.MaterialTemplate(
    site="DR dashboard",
    title=pathlib.Path(__file__).stem.replace('_', ' ').lower(),
    # sidebar=[sidebar],
    main=[bound_get_session_df],
    # sidebar_width=width + 30,
).servable()
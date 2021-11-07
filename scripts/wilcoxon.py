# %%

from scipy.stats import wilcoxon
import pandas as pd
import re

dirr = f'/home/ghales/git/tg-server/output/'
# %%
# Load and format form answers
dfqa = pd.read_csv('output/qa.csv')
cols = dfqa.columns

# Split DFs
dfqa_turing = dfqa[cols[3:26]]
dfqa_qualidade = dfqa[[cols[3], *cols[-22:]]]
dfqa_turing = dfqa_turing.melt(id_vars=[dfqa_turing.columns[0]], value_vars=dfqa_turing.columns[1:])
dfqa_qualidade = dfqa_qualidade.melt(id_vars=[dfqa_qualidade.columns[0]], value_vars=dfqa_qualidade.columns[1:])

clean = lambda x: re.sub('(As amostras foram tocadas por humanos ou máquinas\? \[)|(Quão musical a amostra soa\?) \[|\]','',x).split('.')[0]

dfqa_turing['variable'] = dfqa_turing['variable'].apply(clean)
dfqa_qualidade['variable'] = dfqa_qualidade['variable'].apply(clean)

dfqa_turing = dfqa_turing.rename(columns={'variable': 'sample', 'value': 'guess' })
dfqa_qualidade = dfqa_qualidade.rename(columns={'variable': 'sample', 'value': 'quality' })
dfqa_res = dfqa_turing.copy()
dfqa_res['quality'] = dfqa_qualidade['quality']
dfqa_res = dfqa_res.rename(columns={ 'Seu nível de educação musical': 'level' })
print(len(dfqa_res))
dfqa_res.head()

# %%
# Load experiment data

df_truth = pd.read_csv('output/qa_truth.csv')
df_truth = df_truth.rename(columns={ 'name': 'sample' })
df_truth['sample'] = df_truth['sample'].apply(clean)
df_truth.head()

dfqa_res = dfqa_res.merge(df_truth, on=['sample'], how='left')
len(dfqa_res)
dfqa_res.head()


# %%
# Calculate Wilcoxon of Turing Test

## TODO: Filtering by level would go here
df = dfqa_res.copy()
print(df.level.unique())
# df = df[df['level'] != 'Leigo']
# df = df[df['level'] != 'Aprendiz']
df['hit'] = (df['guess'] == 'Humano') == (df['source'] == 'Dataset')
df['quality'] = df['quality'].apply(lambda x: ['Pouco musical', 'Mais ou menos', 'Muito musical'].index(x))

df_hit_q = df.copy()

def wilcox(col, src1='Baseline', src2='Generation', df_=df):
  [_baseline,_gen] = [
    df_[df_['source'] == src1][col].astype(float), 
    df_[df_['source'] == src2][col].astype(float)
  ]
  return wilcoxon(_gen,_baseline)

print(wilcox('hit'))
print(wilcox('quality'))

# %%
# Calculate Wilcoxon of Generation Comparison

df_orig = pd.read_pickle(f'{dirr}df_final_comparison')

# print(df.reset_index().head())
# df = df.melt(value_vars=['KL-Divergence', 'Overlap'])
# df = df.unstack(['metric']).unstack('source').reset_index()
# df = df.melt(id_vars=['subject','metric'], value_vars=['Estática', 'Dinâmica'])

for m in ['KL-Divergence', 'Overlap']:
  df = df_orig[m]
  df = df.unstack(['metric']).unstack('source').reset_index()
  # df = df.melt(id_vars=['subject','metric'], value_vars=['Estática', 'Dinâmica'])
  # print(df)
  print(wilcoxon(df['Dinâmica'],df['Estática']))
  # print(wilcox('value','Estática','Dinâmica', df))

# for (model, metric), df_ in df.groupby(['subject', 'metric']):
#   print(model, metric)
#   print(wilcox('value','Estática','Dinâmica',df_))

# %%
from plotnine import ggplot, geom_bar, theme_bw, aes, theme_minimal, position_dodge, scale_y_continuous, scales
from plotnine import element_text, theme, ggsave
from textwrap import wrap

dft = df_hit_q[['level', 'hit', 'source']]
dft['level'] = dft['level'].apply(lambda x: '\n'.join(wrap(x, 12, break_long_words=False)))
dft = dft.groupby(['level','source']).mean().reset_index()
cats = dft['level'].unique()[[2,0,3,1]]
dft['level'] = pd.Categorical(dft['level'], categories=cats, ordered=True)
dft = dft.rename(columns={ 'hit': 'Acertos (%)', 'source': 'Origem', 'level': 'Grau de Instrução'})

print(dft.head())

p = (
    ggplot(dft, aes(x="Grau de Instrução", y="Acertos (%)", fill="Origem"))
    + geom_bar(stat="identity",position=position_dodge())
    + scale_y_continuous(labels=lambda l: ["%d%%" % (v * 100) for v in l])
    + theme_minimal()
)

ggsave(plot = p, filename = 'barplot_turing', path=f'{dirr}images')
p


# %%

from plotnine import ggplot, geom_boxplot, theme_bw, aes, theme_minimal, position_dodge, scale_y_continuous, scales
from plotnine import element_text, theme, ggsave, geom_jitter, after_scale, geom_pointrange, geom_errorbar
from plotnine import stat_summary
from textwrap import wrap
import numpy as np

# print(dft.head())

dft = df_hit_q[['level', 'source', 'quality']]
cats = dft['level'].unique()[[2,0,1,3]]
dft['level'] = pd.Categorical(dft['level'], categories=cats, ordered=True)
dft['level'] = dft['level'].apply(lambda x: '\n'.join(wrap(x, 12, break_long_words=False)))
dft = dft.rename(columns={ 'quality': 'Qualidade', 'source': 'Origem', 'level': 'Grau de Instrução'})


p = (ggplot(dft, aes(x='Grau de Instrução', y='Qualidade', fill="Origem")) 
+ stat_summary(fun_y = np.mean, geom = 'bar', position=position_dodge())
+ scale_y_continuous(limits=[0.0,3.0])
+ stat_summary(fun_data = 'mean_sdl', fun_args = {'mult':1}, geom = 'errorbar', position=position_dodge(), width=0.89)
+ theme_minimal()
)

ggsave(plot = p, filename = 'boxplot_quality', path=f'{dirr}images')
p



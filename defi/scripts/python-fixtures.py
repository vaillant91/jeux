"""Read only pure source functions; no pygame import and no source modification."""
from pathlib import Path
import ast, json, random, base64, zlib, string, hashlib
source = Path('../defi_ton_pote.py').read_text(encoding='utf-8-sig')
# The checked-in source has a duplicated incomplete function header. Remove only
# that exact duplicate in memory so AST parsing can isolate the pure functions.
duplicate = 'def dessiner_icone_palette(surface: pygame.Surface, rect: pygame.Rect,\n'
source = source.replace(duplicate + duplicate, duplicate)
names = {'niveau_depart', 'niveau_carte_base', 'valider_niveau', 'encoder_niveau'}
module = ast.parse(source)
selected = [node for node in module.body if isinstance(node, ast.FunctionDef) and node.name in names]
namespace = dict(COLONNES_NIVEAU=40, LIGNES_NIVEAU=11, NIVEAUX_CARTE_BASE=12,
                 SOL=1, PLATEFORME=2, PIC=3, POINT_CONTROLE=4, RESSORT=5, GEMME=6, COEUR=7,
                 THEMES_PARCOURS=('prairie','volcan','glace','desert'), base64=base64, zlib=zlib)
exec(compile(ast.Module(body=selected,type_ignores=[]), '<source-functions>', 'exec'), namespace)
levels = [namespace['niveau_depart']()] + [namespace['niveau_carte_base'](n) for n in range(1,13)]
rngs=[]
for seed in (0, 12345, 2176782335):
    rng=random.Random(seed)
    rngs.append(dict(seed=seed, values=[rng.random() for _ in range(10)], integers=[rng.randint(20,980) for _ in range(10)]))
fixture=dict(levels=levels,codes=[namespace['encoder_niveau'](l) for l in levels],random=rngs)
Path('src/game/fixtures/python.json').write_text(json.dumps(fixture,indent=2),encoding='utf-8')
print('13 Python levels, P4 codes and CPython random streams exported.')

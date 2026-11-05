# Mywebsite — site de Christian Sodara

Site statique (HTML + image).

## Lancer en local
```bash
./scripts/serve.sh          # http://localhost:8080
./scripts/check.sh          # validation HTML + fichiers référencés
```

## Workflow de déploiement
| Branche   | Rôle            | Action automatique                                         |
|-----------|-----------------|------------------------------------------------------------|
| `develop` | développement   | CI : `scripts/check.sh`                                    |
| `test`    | recette         | déploiement sur `https://sodara-cpu.github.io/Mywebsite/test/` |
| `main`    | production      | déploiement sur `https://sodara-cpu.github.io/Mywebsite/`      |

Cycle :
```bash
git checkout develop && git pull
# ... modifications, test local ...
git commit -am "..." && git push            # CI sur develop
git checkout test && git merge develop && git push    # déploiement recette
# vérifier /test/, puis :
git checkout main && git merge test && git push       # mise en production
```
(ou via Pull Requests develop → test → main, qui déclenchent aussi la CI.)

# Spotify-historik

Python-script der henter de sange du streamer på Spotify og gemmer dem i en CSV-fil.

## Opsætning

1. Gå til <https://developer.spotify.com/dashboard> og opret en app.
2. Tilføj Redirect URI `http://127.0.0.1:8888/callback` under appens indstillinger.
3. Installér afhængigheder:
   ```bash
   pip install -r requirements.txt
   ```
4. Sæt dine nøgler som miljøvariabler:
   ```bash
   export SPOTIPY_CLIENT_ID="din-client-id"
   export SPOTIPY_CLIENT_SECRET="din-client-secret"
   ```
   (PowerShell: `$env:SPOTIPY_CLIENT_ID="..."`)

Første gang åbnes browseren, så du kan logge ind og give adgang. Tokenet gemmes i `.cache`.

## Brug

```bash
python spotify_history.py                # gem de seneste 50 afspilninger i spotify_history.csv
python spotify_history.py --now          # vis hvad der spiller lige nu
python spotify_history.py --watch        # bliv ved med at logge (tjekker hvert 10. minut)
python spotify_history.py -o min.csv     # anden outputfil
```

Nye afspilninger tilføjes til CSV-filen, og dubletter springes over, så scriptet trygt
kan køres igen og igen (fx via cron / Opgavestyring).

## Begrænsninger

- Spotify API'et giver kun adgang til de **seneste 50** afspillede numre. Kør med `--watch`
  eller planlæg scriptet jævnligt for at opbygge en fuld historik.
- Podcasts medtages ikke.
- Vil du have hele din historik bagud i tid, kan du anmode om
  "Extended streaming history" under Konto → Privatliv på spotify.com.

<#
  Robust global seeding script
  - Requires backend running at http://localhost:8000
  - Creates many incidents worldwide with lat/lng, varied severities, entities, and multiple tweets
#>

$ErrorActionPreference = 'Stop'
$api = "http://localhost:8000"
Write-Host "Seeding incidents via $api ..." -ForegroundColor Cyan

function New-IncidentFromTweet {
  [CmdletBinding()] param(
    [Parameter(Mandatory)] [hashtable] $Tweet,
    [Parameter(Mandatory)] [string]     $IncidentType,
    [Parameter(Mandatory)] [ValidateSet('low','medium','high','critical')] [string] $Severity,
    [Parameter(Mandatory)] [string]     $Location,
    [Parameter()]           [string[]]  $Entities = @(),
    [Parameter()]           [double]    $Lat,
    [Parameter()]           [double]    $Lng
  )

  $payload = @{
    tweet = $Tweet
    is_disaster_related = $true
    incident_type = $IncidentType
    severity = $Severity
    location = $Location
    key_entities = $Entities
    confidence_score = 0.9
    lat = $Lat
    lng = $Lng
  } | ConvertTo-Json -Depth 8

  return Invoke-RestMethod -Uri "$api/analyze-tweet" -Method POST -ContentType 'application/json' -Body $payload
}

function Add-IncidentTweet {
  [CmdletBinding()] param(
    [Parameter(Mandatory)] [string]     $IncidentId,
    [Parameter(Mandatory)] [hashtable] $Tweet
  )
  $body = $Tweet | ConvertTo-Json -Depth 6
  return Invoke-RestMethod -Uri "$api/incidents/$IncidentId/add-tweet" -Method POST -ContentType 'application/json' -Body $body
}

function New-Tweet {
  param(
    [Parameter(Mandatory)] [string] $Text,
    [Parameter(Mandatory)] [string] $Author,
    [Parameter(Mandatory)] [string] $Id,
    [int] $MinutesAgo = 0,
    [int] $Likes = 0,
    [int] $Retweets = 0,
    [int] $Replies = 0
  )
  $ts = (Get-Date).AddMinutes(-1 * $MinutesAgo).ToUniversalTime().ToString('s') + 'Z'
  return @{
    text = $Text
    author = $Author
    timestamp = $ts
    tweet_id = $Id
    engagement = @{ likes = $Likes; retweets = $Retweets; replies = $Replies }
  }
}

# Global incident dataset
$seedData = @(
  @{ Type='Wildfire'; Severity='critical'; Location='Los Angeles, California'; Lat=34.0522; Lng=-118.2437; Entities=@('Wildfire','LosAngeles','Evacuation'); Tweets=@(
      (New-Tweet -Text 'Massive wildfire near Griffith Park, smoke visible for miles. Evacuation orders expanding. #Wildfire #LA' -Author '@LAUpdates' -Id 'LA-WF-1' -MinutesAgo 10 -Likes 520 -Retweets 210 -Replies 80),
      (New-Tweet -Text '405 freeway slowed due to smoke. Avoid the area. #Traffic #Wildfire' -Author '@LADOT' -Id 'LA-WF-2' -MinutesAgo 22 -Likes 180 -Retweets 65 -Replies 24),
      (New-Tweet -Text 'Fire crews making progress on the eastern flank. Wind shift expected tonight. #LAFD' -Author '@LAFD' -Id 'LA-WF-3' -MinutesAgo 5 -Likes 340 -Retweets 150 -Replies 40)
    ) },
  @{ Type='Flash Flood'; Severity='high'; Location='São Paulo, Brazil'; Lat=-23.5505; Lng=-46.6333; Entities=@('Flood','SaoPaulo','UrbanFlood'); Tweets=@(
      (New-Tweet -Text 'Heavy downpour causing flash floods in central São Paulo. Avoid underpasses. #SP #Flood' -Author '@SPWeather' -Id 'SP-FL-1' -MinutesAgo 35 -Likes 420 -Retweets 190 -Replies 60),
      (New-Tweet -Text 'Bus lines delayed due to flooded avenues. #Transit' -Author '@SPTransit' -Id 'SP-FL-2' -MinutesAgo 20 -Likes 160 -Retweets 70 -Replies 18)
    ) },
  @{ Type='Earthquake'; Severity='medium'; Location='Tokyo, Japan'; Lat=35.6762; Lng=139.6503; Entities=@('Earthquake','Tokyo','Aftershocks'); Tweets=@(
      (New-Tweet -Text 'Light quake felt across Chiyoda and Shinjuku. No damage reports yet. #Earthquake' -Author '@QuakeJP' -Id 'TYO-EQ-1' -MinutesAgo 12 -Likes 210 -Retweets 90 -Replies 12),
      (New-Tweet -Text 'Trains performing safety checks; minor delays expected. #JR' -Author '@JR_East' -Id 'TYO-EQ-2' -MinutesAgo 18 -Likes 95 -Retweets 40 -Replies 7)
    ) },
  @{ Type='Storm'; Severity='high'; Location='Manila, Philippines'; Lat=14.5995; Lng=120.9842; Entities=@('Typhoon','RainBands','FloodRisk'); Tweets=@(
      (New-Tweet -Text 'Typhoon rain bands entering Metro Manila. Expect strong winds and heavy rain. #Typhoon' -Author '@PHWeather' -Id 'MNL-ST-1' -MinutesAgo 28 -Likes 390 -Retweets 160 -Replies 55),
      (New-Tweet -Text 'Classes suspended in multiple districts. Stay safe. #Manila' -Author '@ManilaGov' -Id 'MNL-ST-2' -MinutesAgo 14 -Likes 300 -Retweets 140 -Replies 44)
    ) },
  @{ Type='Wildfire'; Severity='high'; Location='Sydney, Australia'; Lat=-33.8688; Lng=151.2093; Entities=@('Bushfire','Sydney','Smoke'); Tweets=@(
      (New-Tweet -Text 'Bushfire watch near Blue Mountains; smoke drifting east. #NSWfires' -Author '@NSW_RFS' -Id 'SYD-WF-1' -MinutesAgo 42 -Likes 280 -Retweets 120 -Replies 30),
      (New-Tweet -Text 'Air quality advisory in effect for western suburbs. #AQI' -Author '@NSWHealth' -Id 'SYD-WF-2' -MinutesAgo 19 -Likes 145 -Retweets 60 -Replies 22)
    ) },
  @{ Type='Flood'; Severity='critical'; Location='Dhaka, Bangladesh'; Lat=23.8103; Lng=90.4125; Entities=@('RiverFlood','Dhaka','Relief'); Tweets=@(
      (New-Tweet -Text 'River levels above danger mark; several neighborhoods inundated. #DhakaFloods' -Author '@DhakaNews' -Id 'DHA-FL-1' -MinutesAgo 50 -Likes 500 -Retweets 230 -Replies 100),
      (New-Tweet -Text 'Relief centers opening in Uttara and Mirpur. #Relief' -Author '@BDRelief' -Id 'DHA-FL-2' -MinutesAgo 21 -Likes 210 -Retweets 90 -Replies 28)
    ) },
  @{ Type='Earthquake'; Severity='high'; Location='Istanbul, Türkiye'; Lat=41.0082; Lng=28.9784; Entities=@('Marmara','Tremor','Preparedness'); Tweets=@(
      (New-Tweet -Text 'Mild to moderate tremor felt on the European side. #Istanbul' -Author '@AFAD' -Id 'IST-EQ-1' -MinutesAgo 16 -Likes 260 -Retweets 110 -Replies 20),
      (New-Tweet -Text 'Citizens advised to check emergency kits. #Safety' -Author '@IstanbulGov' -Id 'IST-EQ-2' -MinutesAgo 8 -Likes 140 -Retweets 65 -Replies 14)
    ) },
  @{ Type='Storm'; Severity='medium'; Location='Lagos, Nigeria'; Lat=6.5244; Lng=3.3792; Entities=@('CoastalFlood','Lagos','StormSurge'); Tweets=@(
      (New-Tweet -Text 'Coastal flooding reported in Lekki Phase 1 after heavy rains. #LagosFlood' -Author '@LagosUpdates' -Id 'LOS-ST-1' -MinutesAgo 37 -Likes 210 -Retweets 100 -Replies 26),
      (New-Tweet -Text 'Motorists advised to avoid Admiralty Way due to waterlogging. #Traffic' -Author '@LASTMA' -Id 'LOS-ST-2' -MinutesAgo 15 -Likes 120 -Retweets 55 -Replies 10)
    ) },
  @{ Type='Power Outage'; Severity='high'; Location='New York City, USA'; Lat=40.7128; Lng=-74.0060; Entities=@('PowerOutage','NYC','Grid'); Tweets=@(
      (New-Tweet -Text 'Widespread power outage in Lower Manhattan, multiple blocks affected. #NYCOutage' -Author '@NYCAlerts' -Id 'NYC-PO-1' -MinutesAgo 29 -Likes 470 -Retweets 210 -Replies 95),
      (New-Tweet -Text 'Subway service delays due to signal issues from outage. #MTA' -Author '@MTA' -Id 'NYC-PO-2' -MinutesAgo 12 -Likes 260 -Retweets 120 -Replies 33)
    ) },
  @{ Type='Storm'; Severity='high'; Location='Shanghai, China'; Lat=31.2304; Lng=121.4737; Entities=@('Typhoon','Wind','Rain'); Tweets=@(
      (New-Tweet -Text 'Typhoon approaching; gale-force winds recorded along the Bund. #Shanghai' -Author '@SHWeather' -Id 'SHA-ST-1' -MinutesAgo 31 -Likes 390 -Retweets 170 -Replies 62),
      (New-Tweet -Text 'Flights delayed at PVG due to crosswinds. #Travel' -Author '@ShanghaiAirport' -Id 'SHA-ST-2' -MinutesAgo 14 -Likes 150 -Retweets 60 -Replies 18)
    ) },
  @{ Type='Wildfire'; Severity='medium'; Location='Cape Town, South Africa'; Lat=-33.9249; Lng=18.4241; Entities=@('MountainFire','CapeTown','Evacuation'); Tweets=@(
      (New-Tweet -Text 'Fire on Table Mountain slopes; hikers evacuated. #CapeTown' -Author '@CTEmergency' -Id 'CPT-WF-1' -MinutesAgo 45 -Likes 260 -Retweets 120 -Replies 34),
      (New-Tweet -Text 'Choppers water-bombing near Kloof Nek. #Firefighting' -Author '@VWSWildfire' -Id 'CPT-WF-2' -MinutesAgo 18 -Likes 190 -Retweets 80 -Replies 20)
    ) },
  @{ Type='Flood'; Severity='high'; Location='Paris, France'; Lat=48.8566; Lng=2.3522; Entities=@('Seine','FloodWatch','Paris'); Tweets=@(
      (New-Tweet -Text 'Seine levels rising; paths along the river closed. #Paris' -Author '@ParisRegion' -Id 'PAR-FL-1' -MinutesAgo 40 -Likes 230 -Retweets 100 -Replies 22),
      (New-Tweet -Text 'Museums moving artifacts to upper floors as a precaution. #Louvre' -Author '@ParisCulture' -Id 'PAR-FL-2' -MinutesAgo 9 -Likes 180 -Retweets 90 -Replies 28)
    ) },
  @{ Type='Earthquake'; Severity='low'; Location='Mexico City, Mexico'; Lat=19.4326; Lng=-99.1332; Entities=@('Tremor','CDMX','Alert'); Tweets=@(
      (New-Tweet -Text 'Light tremor detected by early warning systems; no damage expected. #SASMEX' -Author '@AlertaSISMO' -Id 'CDMX-EQ-1' -MinutesAgo 11 -Likes 130 -Retweets 60 -Replies 9)
    ) },
  @{ Type='Storm'; Severity='medium'; Location='Dubai, UAE'; Lat=25.2048; Lng=55.2708; Entities=@('Sandstorm','LowVisibility','Advisory'); Tweets=@(
      (New-Tweet -Text 'Sandstorm reduces visibility across major highways. Drive carefully. #Dubai' -Author '@DubaiPoliceHQ' -Id 'DXB-ST-1' -MinutesAgo 24 -Likes 200 -Retweets 95 -Replies 16)
    ) },
  @{ Type='Flood'; Severity='high'; Location='Jakarta, Indonesia'; Lat=-6.2088; Lng=106.8456; Entities=@('Monsoon','Jakarta','Flood'); Tweets=@(
      (New-Tweet -Text 'Monsoon rains trigger flooding in East Jakarta districts. #JakartaFlood' -Author '@JKTNews' -Id 'JKT-FL-1' -MinutesAgo 33 -Likes 270 -Retweets 115 -Replies 40),
      (New-Tweet -Text 'Boats assisting evacuations; avoid non-essential travel. #BNPB' -Author '@BNPB_Indonesia' -Id 'JKT-FL-2' -MinutesAgo 12 -Likes 210 -Retweets 100 -Replies 22)
    ) },
  @{ Type='Tornado'; Severity='critical'; Location='Oklahoma City, USA'; Lat=35.4676; Lng=-97.5164; Entities=@('TornadoWarning','OKC','Shelter'); Tweets=@(
      (New-Tweet -Text 'Tornado on the ground near Moore. Seek shelter immediately! #OKWX' -Author '@NWSNorman' -Id 'OKC-TD-1' -MinutesAgo 6 -Likes 620 -Retweets 300 -Replies 120)
    ) },
  @{ Type='Landslide'; Severity='high'; Location='Bogotá, Colombia'; Lat=4.7110; Lng=-74.0721; Entities=@('Landslide','Bogota','Mountain'); Tweets=@(
      (New-Tweet -Text 'Landslide blocks road to Monserrate; crews en route. #Bogota' -Author '@BogotaTransit' -Id 'BOG-LS-1' -MinutesAgo 27 -Likes 150 -Retweets 60 -Replies 15)
    ) }
)

$created = @()
foreach ($item in $seedData) {
  $first = $item.Tweets[0]
  $resp = New-IncidentFromTweet -Tweet $first -IncidentType $item.Type -Severity $item.Severity -Location $item.Location -Entities $item.Entities -Lat $item.Lat -Lng $item.Lng
  if ($resp.incident_created) {
    $incId = $resp.incident_id
    Write-Host ("Created Incident: {0} ({1}, {2})" -f $incId, $item.Type, $item.Location) -ForegroundColor Green
    $created += $incId
    # Add remaining tweets
    for ($i = 1; $i -lt $item.Tweets.Count; $i++) {
      Add-IncidentTweet -IncidentId $incId -Tweet $item.Tweets[$i] | Out-Null
    }
  } else {
    Write-Warning ("Tweet did not create an incident: {0}" -f $first.Id)
  }
}

$all = Invoke-RestMethod -Uri "$api/incidents" -Method GET
Write-Host ("Seed complete. Incidents created this run: {0}" -f $created.Count) -ForegroundColor Cyan
Write-Host ("Total incidents in DB: {0}" -f $all.Count) -ForegroundColor Cyan
$all | ForEach-Object { Write-Host (" - {0} {1} ({2} tweets)" -f $_.id, $_.incident_type, $_.source_tweets.Count) }
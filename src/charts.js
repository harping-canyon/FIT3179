// Narrative and specification paths for the twelve chart components.
export const charts = [
  {
    "id": "M1",
    "fileLabel": "Country counts",
    "mount": "#hero-chart",
    "title": "Four countries each appear in more than 100 games",
    "description": "Circles count games tagged to each country. Their sizes use the same scale in both maps.",
    "views": [
      {
        "title": "Worldwide",
        "spec": "./charts/country-counts.json",
        "aspectRatio": 1.6
      },
      {
        "title": "Western and central Europe (detail)",
        "spec": "./charts/country-counts-europe.json",
        "aspectRatio": 1.15
      }
    ],
    "insight": "Three of the five most frequently tagged countries are European: the UK, France and Germany."
  },
  {
    "id": "M2",
    "fileLabel": "City locations",
    "mount": "#city-chart",
    "title": "Nearly two-thirds of the mapped cities are in Europe",
    "description": "One dot per city. Dot size is constant, even when several games refer to the same city.",
    "views": [
      {
        "title": "Worldwide",
        "spec": "./charts/cities.json",
        "aspectRatio": 1.6
      },
      {
        "title": "Western and central Europe (detail)",
        "spec": "./charts/cities-europe.json",
        "aspectRatio": 1.15
      }
    ],
    "insight": ""
  },
  {
    "id": "M3",
    "fileLabel": "Wargame shares",
    "mount": "#share-chart",
    "title": "Military conflict accounts for 56% of Germany’s tagged games",
    "description": "Wargames as a percentage of each country’s tagged games. Grey countries have fewer than 20 games or no country tag.",
    "views": [
      {
        "title": "Worldwide (share within each country)",
        "spec": "./charts/wargame-share.json",
        "aspectRatio": 1.6
      },
      {
        "title": "Western and central Europe (same scale)",
        "spec": "./charts/wargame-share-europe.json",
        "aspectRatio": 1.15
      }
    ],
    "insight": "Germany has roughly three times as many Wargames as Japan, despite fewer tagged games overall."
  },
  {
    "id": "C4",
    "fileLabel": "Themes by country",
    "minWidth": 550,
    "mount": "#category-chart",
    "title": "City building appears in 19% of games tagged Italy",
    "description": "Italy’s share is more than twice Germany’s 8%. Percentages are calculated within countries with at least 20 tagged games; categories overlap.",
    "spec": "./charts/themes.json",
    "insight": ""
  },
  {
    "id": "C6",
    "fileLabel": "Complexity",
    "layout": "aside",
    "mount": "#complexity-chart",
    "title": "Wargames receive higher complexity scores",
    "description": "Users score complexity from 1 (simple) to 5 (complex). Each box contains the middle half of the scores; its white line marks the median.",
    "spec": "./charts/complexity.json",
    "insight": "The distributions overlap: some Wargames receive lower complexity scores than many other games."
  },
  {
    "id": "C11",
    "fileLabel": "Country rankings",
    "minWidth": 650,
    "mount": "#rank-chart",
    "spec": "./charts/country-rankings.json",
    "title": "Japan ranks first outside Wargames; France and Germany lead within them",
    "description": "Rankings for the 12 countries with at least 20 tagged games. Brackets show counts; ties share a rank.",
    "insight": ""
  },
  {
    "id": "C5",
    "fileLabel": "Common mechanics",
    "layout": "aside",
    "minWidth": 500,
    "mount": "#mechanics-chart",
    "spec": "./charts/mechanics.json",
    "title": "Nearly one game in three involves managing a hand",
    "insight": ""
  },
  {
    "id": "C7",
    "fileLabel": "Playing time",
    "layout": "aside",
    "minWidth": 610,
    "mount": "#time-chart",
    "spec": "./charts/playing-time.json",
    "title": "The median Wargame lists two hours of play",
    "description": "Listed playing times up to six hours. Width shows the relative concentration within each group; labels mark the medians.",
    "insight": "About half the recorded playing times are an hour or less (428 of 854)."
  },
  {
    "id": "C8",
    "fileLabel": "Ratings",
    "mount": "#ratings-chart",
    "spec": "./charts/ratings.json",
    "title": "Ticket to Ride scores 7.4/10 at a complexity of 1.8/5",
    "description": "Each dot is a game; darker patches contain more games. Ratings are BoardGameGeek users’ average scores out of ten.",
    "insight": "Ticket to Ride scores 7.4/10 and is less complex than 84% of the games in this sample."
  },
  {
    "id": "C9",
    "fileLabel": "Player counts",
    "minWidth": 650,
    "mount": "#players-chart",
    "spec": "./charts/player-counts.json",
    "title": "Only 13 games are strictly for one player",
    "description": "Area counts games, grouped by solo support and then maximum player count. Each game appears once.",
    "insight": "227 of the 240 games with a solo option also support other players. Only 13 are solo-only."
  },
  {
    "id": "C10",
    "fileLabel": "Game profiles",
    "minWidth": 550,
    "mount": "#ranges-chart",
    "spec": "./charts/game-profiles.json",
    "title": "Twilight Struggle takes longer but seats fewer players than Ticket to Ride",
    "description": "Six games compared on complexity, listed playing time and maximum player count. Each axis uses a different scale.",
    "insight": "Longer games do not necessarily seat more people: Power Grid lists two hours for six; Great Western Trail, two and a half hours for four."
  },
  {
    "id": "C12",
    "fileLabel": "Shared mechanics",
    "mount": "#network-chart",
    "minWidth": 650,
    "spec": "./charts/shared-mechanics.json",
    "title": "101 games pair hand management with set collection",
    "description": "Connections among the five most common mechanics. Circle area counts games using a mechanic; line width counts games using both. More than two in five games with set collection also involve managing a hand.",
    "insight": ""
  }
];

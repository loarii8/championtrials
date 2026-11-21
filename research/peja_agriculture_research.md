# Peja Agriculture: Research and Data Notes

**Research accessed:** 21 November 2026  
**Scope:** Publicly documented agriculture, food traditions, locations, prices, and reusable local imagery relevant to Peja and Rugova.  
**Data policy:** This is regional context, not a directory of marketplace members. No researched business is represented as a registered PejaMarket farmer.

## Methodology

Reviewed Kosovo Agency of Statistics (ASK) Agricultural Census 2014 tables, Peja Municipality agriculture and tourism pages, Kosovo Ministry of Agriculture program pages, ASK's national agricultural-price table, a dated local-food article, and Wikimedia Commons file pages. Records retain their source URLs and access date in the accompanying JSON files. Image licenses and attribution were checked on the Commons file pages; downloaded copies are stored under `assets/`.

The evidence was not sufficient to verify a named farm or farmer in Peja, a current local price list, contemporary product availability, or permission to reuse photographs of Peja farmers or farms. Those gaps are left explicit rather than filled with assumptions. Records imported from these files require an administrator's approval before researched text is published.

## Findings specific to Peja Municipality

### Agricultural census (2014)

ASK's 2014 Agricultural Census recorded 6,010 agricultural holdings using 21,024.91 hectares of utilized agricultural area in Peja. Its orchard table records 233.02 hectares of orchards, including 176.70 hectares of apples, 28.52 hectares of plums, and 8.92 hectares of pears. The livestock table records 18,199 cattle, including 8,893 dairy cows, as well as 8,599 sheep and 1,420 goats.

These are historical census figures, not current production, sales, availability, or farmer counts. The application labels the figures with their 2014 reference year.

- [ASK Agricultural Census 2014 — land use, Table 2.22](https://askdata.rks-gov.net/api/v1/en/ASKdata/Agriculture/Agriculture%20census%202014/2%20Land%20Use/Tabla%202_22.px)
- [ASK Agricultural Census 2014 — orchards, Table 2.16](https://askdata.rks-gov.net/api/v1/en/ASKdata/Agriculture/Agriculture%20census%202014/2%20Land%20Use/Tabla%202_16.px)
- [ASK Agricultural Census 2014 — livestock, Table 3.3](https://askdata.rks-gov.net/api/v1/en/ASKdata/Agriculture/Agriculture%20census%202014/3%20Livestock/Tabela%203_3.px)

### Municipality-documented geography and food traditions

Peja Municipality describes Rugova as northwest of Peja and says the region includes 15 villages. The municipal tourism material names Restaurant Bjeshka at Garuzhda (Shtypeq i Madh) and lists foods including milk, cheese, yogurt, honey, mountain tea, lakror, flija, and kaçamak. This documents the municipality's tourism description; it does not prove that a particular farm produces these foods or that they are currently available.

- [Peja Municipality — Rugova](https://peja.rks-gov.net/rugova/)
- [Peja Municipality — natural resources and tourist resources](https://peja.rks-gov.net/burimet-natyrore-resurset-turistike/)

Restaurant Bjeshka is included only as a **municipality-listed food venue**, not as a farm, producer, PejaMarket seller, or endorsed business. Its current operating status and sourcing are not independently verified.

### Historical sourcing reference

A 2020 Prishtina Insight article reports that a Prishtina restaurant worked with small farmers and that an unnamed farmer in Peja supplied squash, carrots, and peppers. The farmer is not identified, and the article does not establish a current supply relationship. It is not imported as a farmer or business listing.

- [Prishtina Insight — “Thana Rosticeri: Bringing the Farm to Your Plate”](https://prishtinainsight.com/guide/thana-rosticeri-bringing-the-farm-to-your-plate/)

## Wider Kosovo context and prices

The Ministry of Agriculture publishes national pages for direct payments, grants, and subsidies. These are national program information, not evidence of a current Peja-specific award, beneficiary, or eligibility status.

- [Kosovo Ministry of Agriculture — direct payments](https://mbpzhr.rks-gov.net/pagesat-direkte/)
- [Kosovo Ministry of Agriculture — grants](https://mbpzhr.rks-gov.net/grante/)
- [Kosovo Ministry of Agriculture — subsidies](https://mbpzhr.rks-gov.net/subvencione/)

ASK's agricultural prices table is national and does not provide a Peja municipality dimension in the reviewed metadata. Its catalog coverage and table coverage differ. No value is imported or presented as a current local Peja price.

- [ASK — Quarterly Output Price Index and Prices in Agriculture](https://askdata.rks-gov.net/api/v1/en/ASKdata/Agriculture/Agriculture%20Price%20and%20Price%20Index/Indeksi%20i%20%C3%87mimeve%20t%C3%AB%20Prodhimit%20dhe%20%C3%87mimet%20n%C3%AB%20Bujq%C3%ABsi/Quarterly%20Output%20Price%20Index%20and%20Prices%20in%20Agriculture/ICPB04.px)
- [ASKdata portal](https://askdata.rks-gov.net/pxweb/sq/ASKdata/)

All regional product references therefore have a null price. They are research references, not stock-bearing listings; a live seller must set their own price.

## Farmers, farms, and businesses

No named Peja farmer, farm, or agricultural cooperative was independently verified in the reviewed sources. The public dataset `farmers.json` is intentionally empty. The municipal tourism-listed restaurant and the unnamed farmer in the 2020 article are not represented as a farm account or PejaMarket member. No private personal details were collected and no business was contacted.

The application keeps three concepts distinct:

1. **Registered farmer:** an account created by its owner and managed through the farmer dashboard.
2. **Researched public record:** source-linked context, held for administrator review and never converted into an account.
3. **Demonstration data:** fictional seeded accounts, listings, and prices, visibly marked as demo data.

## Product references and locations

The supported research references are apples, plums, and pears (2014 orchard census); dairy cattle, sheep, and goats (2014 livestock census); municipal-tourism-listed food traditions; and the limited historical report of squash, carrots, and peppers supplied by an unnamed Peja farmer. The evidence does not establish present-day supply or seasonality. Tomatoes, potatoes, and other products are not described as Peja-origin products solely because they appear in generic product imagery.

Rugova is described by the municipality as northwest of Peja and as a region of 15 villages. Garuzhda / Shtypeq i Madh is named in the municipal tourism listing for Restaurant Bjeshka. No exact private farm addresses or invented coordinates are used.

## Authentic local images and reuse

Three downloaded images depict Peja-region scenery or retail, not agriculture:

- **Rugova Canyon — Peja, Kosovo:** local landscape image, photographer SUHEJLO, CC BY 4.0 ([source page](https://commons.wikimedia.org/wiki/File:Rugova_Canyon_%E2%80%93_Peja,_Kosovo.jpg)). Credit and license link are displayed with the image.
- **Bogë Ski Center — Rugova Mountains:** local winter/ski landscape image, photographer SUHEJLO, CC BY 4.0 ([source page](https://commons.wikimedia.org/wiki/File:Boge_Ski-Center_from_the_sky_in_Rugova_Mountains_in_Kosovo.jpg)). It is not presented as a farm photograph.
- **Kipper supermarket, Peja (2025):** local retail photograph, photographer Bdx, CC0 1.0 ([source page](https://commons.wikimedia.org/wiki/File:Kipper_supermarket,_Peja,_2025.jpg)). It is labeled as a retail scene, not a farm or produce image.

Generic product photographs are separately labeled as illustrative and not from Peja or a seller's inventory:

- Red apple — Abhijit Tembhekar, CC BY 2.0 ([source page](https://commons.wikimedia.org/wiki/File:Red_Apple.jpg)).
- Organic home-grown tomatoes (photographed in New Zealand) — Michal Klajban, CC BY-SA 4.0 ([source page](https://commons.wikimedia.org/wiki/File:Organic_home-grown_tomatoes_-_unripe_to_ripe.jpg)).
- Red and yellow peppers in water — ulleo, CC0 1.0 ([source page](https://commons.wikimedia.org/wiki/File:Peppers_in_water.jpg)).
- Russet potato — ZooFari, public domain as indicated on the Commons file page ([source page](https://commons.wikimedia.org/wiki/File:Russet_potato_cultivar_with_sprouts.jpg)).
- Belper Mürggel cheese (Switzerland) — Yann Forget, CC BY-SA 4.0 ([source page](https://commons.wikimedia.org/wiki/File:Belper_M%C3%BCrggel_B,_WikiCheese_Lausanne.jpg)).
- French monofloral honey jars — Hayden Soloviev, CC BY 4.0 ([source page](https://commons.wikimedia.org/wiki/File:Three_French_monofloral_honey_jars.jpg)).
- Sour cherries — Nicubunu, CC BY-SA 3.0 ([source page](https://commons.wikimedia.org/wiki/File:Sour_cherries.jpg)).
- Pears — Rhododendrites, CC BY-SA 4.0 ([source page](https://commons.wikimedia.org/wiki/File:Four_pears.jpg)).
- Cucumbers — Muu-karhu, CC BY-SA 3.0 ([source page](https://commons.wikimedia.org/wiki/File:Kurkkuja.jpg)).
- Spinach leaves — Nillerdk, CC BY 3.0 ([source page](https://commons.wikimedia.org/wiki/File:Spinach_leaves.jpg)).
- Chicken eggs — Krzysztof Golik, CC BY-SA 4.0 ([source page](https://commons.wikimedia.org/wiki/File:Egg_cartons_with_chicken_eggs_02.jpg)).
- Buckwheat flour — Veganbaking.net, CC BY-SA 2.0 ([source page](https://commons.wikimedia.org/wiki/File:Buckwheat_Flour_%284107890675%29.jpg)).
- Corn kernels — Danielgrad, CC BY-SA 3.0 ([source page](https://commons.wikimedia.org/wiki/File:Corn_kernels.jpg)).
- Carrots — Bukky658, CC BY-SA 4.0 ([source page](https://commons.wikimedia.org/wiki/File:A_tray_of_fresh_carrots.jpg)).
- Boston brown bread — Daderot, CC0 1.0 ([source page](https://commons.wikimedia.org/wiki/File:Boston_Brown_Bread_loaf_-_Massachusetts.jpg)).
- Fresh herb bundle from a San Francisco market — HaJunkiyada, CC BY-SA 4.0 ([source page](https://commons.wikimedia.org/wiki/File:Liat_Portal_for_Foodie_Disorder_-_Fresh_Herb_Bundle_from_San_Francisco_Farmers_Market.jpg)).
- Strawberry-plum jam — DanielPenfield, CC BY-SA 4.0 ([source page](https://commons.wikimedia.org/wiki/File:MonroeCountyFair2018StrawberryPlumJam.jpg)).
- Bulgarian yogurt — Rainer Zenz (assumed by Wikimedia Commons), CC BY-SA 3.0 ([source page](https://commons.wikimedia.org/wiki/File:Joghurt.jpg)).

The generic photographs are matched to seeded example products where a suitable image was available; they are not claims about Peja products or seller inventory. Listings without a suitable image use a category-specific visual fallback instead of an unrelated photograph. Each local file is optimized by applying source EXIF orientation where present, resizing, and JPEG re-encoding; image content is otherwise unchanged. Attribution, license, source page, access date, and local asset path are retained in `images.json` and the database. No verified, reusable image of a Peja farmer, farm, or locally produced food was found.

## Information not verified

- Current Peja farm/business registry or named producer directory.
- Current Peja product supply, farm output, or inventory.
- Current Peja-level advertised prices or market-price series.
- Current municipal grants/beneficiaries.
- Current sourcing or operating status for the municipal tourism-listed food venue.
- Exact farm locations suitable for a public map.
- Reusable documentary photographs of Peja farms, farmers, or products.
- Product seasonality specific to Peja.

The application must continue to label demo data clearly, keep research records unpublished until an administrator approves them, and avoid using generic imagery as evidence of product origin.

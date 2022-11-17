// @ts-ignore
const fs = require("fs");

import {
  createAttribute,
  createAttributeProductLinks,
  createAttributeValue,
  createProduct,
} from "./factories";
import { ticketProductType, ticketsCategory } from "./static-objects";

const productSlugAttribute = createAttribute({
  name: "Product Slug",
  slug: "product-slug",
  input_type: "dropdown",
  isRequired: false,
});
const streamTypeAttribute = createAttribute({
  name: "Stream Type",
  slug: "stream-type",
  input_type: "dropdown",
  isRequired: true,
});
const ticketTypeAttribute = createAttribute({
  name: "Ticket Type",
  slug: "ticket-type",
  input_type: "dropdown",
  isRequired: true,
});
const leaguesAttribute = createAttribute({
  name: "Leagues",
  slug: "leagues",
  input_type: "multiselect",
  isRequired: false,
});
const teamsAttribute = createAttribute({
  name: "Teams",
  slug: "teams",
  input_type: "multiselect",
  isRequired: false,
});
const startDateAttribute = createAttribute({
  name: "Start Time",
  slug: "start-time",
  input_type: "date",
  isRequired: false,
});
const endDateAttribute = createAttribute({
  name: "End Time",
  slug: "end-time",
  input_type: "date",
  isRequired: false,
});

const attributeLinks = [
  productSlugAttribute,
  streamTypeAttribute,
  ticketTypeAttribute,
  leaguesAttribute,
  teamsAttribute,
  startDateAttribute,
  endDateAttribute
].map((attribute) => createAttributeProductLinks(attribute))
  .flat();

const ticketTypeValues = [
  { name: "Single", slug: "single" },
  { name: "Season", slug: "season" },
  { name: "Timed Season", slug: "timed-season" },
  { name: "Month", slug: "month" },
  { name: "Day", slug: "day" },
].map((config) => createAttributeValue(ticketTypeAttribute, config));

const [
  singleAttribute,
  seasonAttribute,
  timedSeasonAttribute,
  monthAttribute,
  dayAttribute
] = ticketTypeValues;

const streamTypeValues = [
  { name: "Game", slug: "game" },
  { name: "Video", slug: "video" },
].map((config) => createAttributeValue(streamTypeAttribute, config));
const [streamTypeGame, streamTypeVideo] = streamTypeValues;

const productSlugValues = [
  { name: "Single", slug: "single" },
  { name: "Season", slug: "season" },
  { name: "Cup", slug: "cup" },
  { name: "Regular Season", slug: "regular-season" },
  { name: "Playoffs", slug: "playoffs" },
  { name: "Month", slug: "month" },
  { name: "Day", slug: "day" }
].map((config) => createAttributeValue(productSlugAttribute, config));

const [
  singleProductSlug,
  seasonProductSlug,
  cupProductSlug,
  regularSeasonProductSlug,
  playoffsProductSlug,
  monthProductSlug,
  dayProductSlug
] = productSlugValues;

const allTeamValue = createAttributeValue(teamsAttribute, {
  name: "All Teams",
  slug: "all-teams",
});

const teamValues = [
  { name: "ASH", slug: "ash" },
  { name: "ECB", slug: "ecb" },
  { name: "EHC", slug: "ehc" },
  { name: "FAS", slug: "fas" },
  { name: "GHE", slug: "ghe" },
  { name: "JES", slug: "jes" },
  { name: "SWL", slug: "swl" },
  { name: "KA2", slug: "ka2" },
  { name: "KEC", slug: "kec" },
  { name: "PUS", slug: "pus" },
  { name: "RBJ", slug: "rbj" },
  { name: "RIT", slug: "rit" },
  { name: "SGC", slug: "sgc" },
  { name: "VEU", slug: "veu" },
  { name: "WSV", slug: "wsv" },
  { name: "HKO", slug: "hko" },
  { name: "HCB", slug: "hcb" },
  { name: "VSV", slug: "vsv" },
  { name: "BWI", slug: "bwi" },
  { name: "HCI", slug: "hci" },
  { name: "G99", slug: "g99" },
  { name: "VIC", slug: "vic" },
  { name: "RBS", slug: "rbs" },
  { name: "KAC", slug: "kac" },
  { name: "DEC", slug: "dec" },
  { name: "AVS", slug: "avs" },
  { name: "BRC", slug: "brc" },
  { name: "AEV", slug: "aev" },
  { name: "PEC", slug: "pec" }
].map((config) => createAttributeValue(teamsAttribute, config));

const leagueValues = [
  { name: "ICE", slug: "ice" },
  { name: "AHL", slug: "ahl" },
  { name: "DOL", slug: "dol" },
].map((config) => createAttributeValue(leaguesAttribute, config));

const [
  iceLeague,
  ahlLeague,
  dolLeague
] = leagueValues;

const startDateValues = [
  { name: "2022-09-01", slug: "date-1", dateTime: "2022-09-01 00:00:00.000000Z" },
  { name: "2022-02-01", slug: "date-3", dateTime: "2022-02-01 00:00:00.000000Z" },
].map((config) => createAttributeValue(startDateAttribute, config, config.dateTime));

const endDateValues = [
  { name: "2022-01-31", slug: "date-2", dateTime: "2022-01-31 00:00:00.000000Z" },
  { name: "2022-04-16", slug: "date-4", dateTime: "2022-04-16 00:00:00.000000Z" },
].map((config) => createAttributeValue(endDateAttribute, config, config.dateTime));

const [
  regularStart,
  playoffsStart,
] = startDateValues;

const [
  regularEnd,
  playoffsEnd,
] = endDateValues;

// SINGLE TICKETS
const singleProducts = teamValues
  .map((team) =>
    createProduct({
      name: "Single",
      postfix: `- ${team.fields.name}`,
      postfixSlug: `-${team.fields.slug}`,
      price: "4.900",
      attributes: [
        { attribute: ticketTypeAttribute, values: [singleAttribute] },
        { attribute: teamsAttribute, values: [team] },
        { attribute: streamTypeAttribute, values: [streamTypeGame] },
        { attribute: productSlugAttribute, values: [singleProductSlug] },
      ],
    })
  )
  .flat();

// REGULAR SEASON TICKETS
const regularSeasonProducts = teamValues
  .map((team) =>
    createProduct({
      name: "Regular Season",
      postfix: `- ${team.fields.name}`,
      postfixSlug: `-${team.fields.slug}`,
      price: "159.000",
      attributes: [
        { attribute: ticketTypeAttribute, values: [timedSeasonAttribute] },
        { attribute: teamsAttribute, values: [team] },
        { attribute: leaguesAttribute, values: [iceLeague, ahlLeague] },
        { attribute: streamTypeAttribute, values: [streamTypeGame] },
        { attribute: productSlugAttribute, values: [regularSeasonProductSlug] },
        { attribute: startDateAttribute, values: [regularStart] },
        { attribute: endDateAttribute, values: [regularEnd] },
      ],
    })
  )
  .flat();

// PLAYOFF SEASON TICKETS
const playoffsProducts = teamValues
  .map((team) =>
    createProduct({
      name: "Playoffs",
      postfix: `- ${team.fields.name}`,
      postfixSlug: `-${team.fields.slug}`,
      price: "89.000",
      attributes: [
        { attribute: ticketTypeAttribute, values: [timedSeasonAttribute] },
        { attribute: teamsAttribute, values: [team] },
        { attribute: leaguesAttribute, values: [iceLeague, ahlLeague] },
        { attribute: streamTypeAttribute, values: [streamTypeGame] },
        { attribute: productSlugAttribute, values: [playoffsProductSlug] },
        { attribute: startDateAttribute, values: [playoffsStart] },
        { attribute: endDateAttribute, values: [playoffsEnd] },
      ],
    })
  )
  .flat();

// TEAM SEASON TICKETS
const seasonProducts = teamValues
  .map((team) =>
    createProduct({
      name: "Season",
      postfix: `- ${team.fields.name}`,
      postfixSlug: `-${team.fields.slug}`,
      price: "199.000",
      attributes: [
        { attribute: ticketTypeAttribute, values: [seasonAttribute] },
        { attribute: teamsAttribute, values: [team] },
        { attribute: streamTypeAttribute, values: [streamTypeGame] },
        { attribute: productSlugAttribute, values: [seasonProductSlug] },
      ],
    })
  )
  .flat();

// GLOBAL SEASON TICKET (for all leagues)
seasonProducts.push(
  ...createProduct({
    name: "Season",
    postfix: "",
    postfixSlug: "",
    price: "299.000",
    attributes: [
      { attribute: ticketTypeAttribute, values: [seasonAttribute] },
      { attribute: teamsAttribute, values: [allTeamValue] },
      { attribute: streamTypeAttribute, values: [streamTypeGame] },
      { attribute: productSlugAttribute, values: [seasonProductSlug] },
    ],
  })
);

// CUP TICKET
seasonProducts.push(
  ...createProduct({
    name: "Cup",
    postfix: "",
    postfixSlug: "",
    price: "19.900",
    attributes: [
      { attribute: ticketTypeAttribute, values: [seasonAttribute] },
      { attribute: teamsAttribute, values: [allTeamValue] },
      { attribute: streamTypeAttribute, values: [streamTypeGame] },
      { attribute: productSlugAttribute, values: [cupProductSlug] },
      { attribute: leaguesAttribute, values: [dolLeague] },
    ],
  })
);

// [IGNORE] timed tickets are not necessary for testing at the moment
// const dayProducts = leagueValues
//   .map((league) =>
//     createProduct({
//       name: "Day",
//       postfix: `- ${league.fields.name}`,
//       postfixSlug: `-${league.fields.slug}`,
//       price: "12.500",
//       attributes: [
//         { attribute: ticketTypeAttribute, values: [dayAttribute] },
//         { attribute: leaguesAttribute, values: [league] },
//         { attribute: streamTypeAttribute, values: [streamTypeGame] },
//         { attribute: productSlugAttribute, values: [dayProductSlug] },
//       ],
//     })
//   )
//   .flat();
//
// const monthProducts = leagueValues
//   .map((league) => {
//     const products = teamValues.map((team) =>
//       createProduct({
//         name: "Month",
//         postfix: `- ${league.fields.name} - ${team.fields.name}`,
//         postfixSlug: `-${league.fields.slug}-${team.fields.slug}`,
//         price: "49.000",
//         attributes: [
//           { attribute: ticketTypeAttribute, values: [monthAttribute] },
//           { attribute: leaguesAttribute, values: [league] },
//           { attribute: teamsAttribute, values: [team] },
//           { attribute: streamTypeAttribute, values: [streamTypeGame] },
//           { attribute: productSlugAttribute, values: [monthProductSlug] },
//         ],
//       })
//     );
//
//     products.push(
//       createProduct({
//         name: "Month",
//         price: "89.000",
//         postfix: `- ${league.fields.name}`,
//         postfixSlug: `-${league.fields.slug}`,
//         attributes: [
//           { attribute: ticketTypeAttribute, values: [monthAttribute] },
//           { attribute: leaguesAttribute, values: [league] },
//           { attribute: teamsAttribute, values: [allTeamValue] },
//           { attribute: streamTypeAttribute, values: [streamTypeGame] },
//           { attribute: productSlugAttribute, values: [monthProductSlug] },
//         ],
//       })
//     );
//
//     return products;
//   })
//   .flat()
//   .flat();

const result = [
  ticketsCategory,
  ticketProductType,
  productSlugAttribute,
  ticketTypeAttribute,
  streamTypeAttribute,
  leaguesAttribute,
  teamsAttribute,
  startDateAttribute,
  endDateAttribute,
  allTeamValue,
  ...attributeLinks,
  ...streamTypeValues,
  ...ticketTypeValues,
  ...teamValues,
  ...leagueValues,
  ...productSlugValues,
  ...startDateValues,
  ...endDateValues,
  ...singleProducts,
  ...regularSeasonProducts,
  ...playoffsProducts,
  ...seasonProducts,
  // ...dayProducts,
  // ...monthProducts,
];

fs.writeFile("./result.json", JSON.stringify(result), (err) => {
  if (err) {
    console.log(err);
  }
});

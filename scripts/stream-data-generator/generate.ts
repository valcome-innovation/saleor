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
const teamRestrictionAttribute = createAttribute({
  name: "Team Restriction",
  slug: "team-restriction",
  input_type: "dropdown",
  isRequired: true,
});

const attributeLinks = [
  productSlugAttribute,
  streamTypeAttribute,
  ticketTypeAttribute,
  leaguesAttribute,
  teamsAttribute,
  teamRestrictionAttribute
].map((attribute) => createAttributeProductLinks(attribute))
  .flat();

const ticketTypeValues = [
  { name: "Single", slug: "single" },
  { name: "Season", slug: "season" },
  { name: "Timed Season", slug: "timed-season" },
  { name: "Timed", slug: "timed" },
].map((config) => createAttributeValue(ticketTypeAttribute, config));

const [
  singleAttribute,
  seasonAttribute,
  timedSeasonAttribute,
  timedAttribute,
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
  { name: "Regular Season (Away)", slug: "regular-season-away" },
  { name: "Playoffs", slug: "playoffs" },
  { name: "Playoffs (Away)", slug: "playoffs-away" },
  { name: "Month", slug: "month" },
  { name: "Day", slug: "day" }
].map((config) => createAttributeValue(productSlugAttribute, config));

const [
  singleProductSlug,
  seasonProductSlug,
  cupProductSlug,
  regularSeasonProductSlug,
  regularSeasonAwayProductSlug,
  playoffsProductSlug,
  playoffsAwayProductSlug,
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

const teamRestrictionValues = [
  { name: "Allow Both", slug: "allow-both" },
  { name: "Home Only", slug: "home-only" },
  { name: "Guest Only", slug: "guest-only" },
].map((config) => createAttributeValue(teamRestrictionAttribute, config));

const [
  allowBoth,
  homeOnly,
  guestOnly
] = teamRestrictionValues;

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
        { attribute: teamRestrictionAttribute, values: [allowBoth] },
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
        { attribute: teamRestrictionAttribute, values: [allowBoth] },
      ],
    })
  )
  .flat();

// REGULAR SEASON TICKETS (AWAY)
const regularSeasonAwayProducts = teamValues
  .map((team) =>
    createProduct({
      name: "Regular Season (Away)",
      postfix: `- ${team.fields.name}`,
      postfixSlug: `-${team.fields.slug}`,
      price: "79.500",
      attributes: [
        { attribute: ticketTypeAttribute, values: [timedSeasonAttribute] },
        { attribute: teamsAttribute, values: [team] },
        { attribute: leaguesAttribute, values: [iceLeague, ahlLeague] },
        { attribute: streamTypeAttribute, values: [streamTypeGame] },
        { attribute: productSlugAttribute, values: [regularSeasonAwayProductSlug] },
        { attribute: teamRestrictionAttribute, values: [guestOnly] },
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
        { attribute: teamRestrictionAttribute, values: [allowBoth] },
      ],
    })
  )
  .flat();

// PLAYOFF SEASON TICKETS (AWAY)
const playoffsAwayProducts = teamValues
  .map((team) =>
    createProduct({
      name: "Playoffs (Away)",
      postfix: `- ${team.fields.name}`,
      postfixSlug: `-${team.fields.slug}`,
      price: "44.500",
      attributes: [
        { attribute: ticketTypeAttribute, values: [timedSeasonAttribute] },
        { attribute: teamsAttribute, values: [team] },
        { attribute: leaguesAttribute, values: [iceLeague, ahlLeague] },
        { attribute: streamTypeAttribute, values: [streamTypeGame] },
        { attribute: productSlugAttribute, values: [playoffsAwayProductSlug] },
        { attribute: teamRestrictionAttribute, values: [guestOnly] },
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
        { attribute: teamRestrictionAttribute, values: [allowBoth] },
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
      { attribute: teamRestrictionAttribute, values: [allowBoth] },
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
      { attribute: teamRestrictionAttribute, values: [allowBoth] },
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
  allTeamValue,
  teamRestrictionAttribute,
  ...attributeLinks,
  ...streamTypeValues,
  ...ticketTypeValues,
  ...teamValues,
  ...leagueValues,
  ...productSlugValues,
  ...teamRestrictionValues,
  ...singleProducts,
  ...regularSeasonProducts,
  ...regularSeasonAwayProducts,
  ...playoffsProducts,
  ...playoffsAwayProducts,
  ...seasonProducts,
  // ...dayProducts,
  // ...monthProducts,
];

fs.writeFile("./result.json", JSON.stringify(result), (err) => {
  if (err) {
    console.log(err);
  }
});

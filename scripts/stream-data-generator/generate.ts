// @ts-ignore
const fs = require("fs");

import {
  createAttribute,
  createAttributeProductLinks,
  createAttributeValue,
  createProduct,
} from "./factories";
import { ticketProductType, ticketsCategory } from "./static-objects";

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

const attributeLinks = [streamTypeAttribute, ticketTypeAttribute, leaguesAttribute, teamsAttribute]
  .map((attribute) => createAttributeProductLinks(attribute))
  .flat();

const ticketTypeValues = [
  { name: "Single", slug: "single" },
  { name: "Season", slug: "season" },
  { name: "Month", slug: "month" },
  { name: "Day", slug: "day" },
].map((config) => createAttributeValue(ticketTypeAttribute, config));

const [singleAttribute, seasonAttribute, monthAttribute, dayAttribute] = ticketTypeValues;

const streamTypeValues = [
  { name: "Game", slug: "game" },
  { name: "Video", slug: "video" },
].map((config) => createAttributeValue(streamTypeAttribute, config));
const [streamTypeGame, streamTypeVideo] = streamTypeValues;

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
].map((config) => createAttributeValue(teamsAttribute, config));

const leagueValues = [
  { name: "ICE", slug: "ice" },
  { name: "AHL", slug: "ahl" },
].map((config) => createAttributeValue(leaguesAttribute, config));

const singleGameProducts = teamValues
  .map((team) =>
    createProduct({
      name: "Single-Game",
      postfix: `- ${team.fields.name}`,
      postfixSlug: `-${team.fields.slug}`,
      price: "4.900",
      attributes: [
        { attribute: ticketTypeAttribute, values: [singleAttribute] },
        { attribute: teamsAttribute, values: [team] },
        { attribute: streamTypeAttribute, values: [streamTypeGame] },
      ],
    })
  )
  .flat();

const singleVideoProducts = teamValues
  .map((team) =>
    createProduct({
      name: "Single-Video",
      postfix: `- ${team.fields.name}`,
      postfixSlug: `-${team.fields.slug}`,
      price: "2.900",
      attributes: [
        { attribute: ticketTypeAttribute, values: [singleAttribute] },
        { attribute: teamsAttribute, values: [team] },
        { attribute: streamTypeAttribute, values: [streamTypeVideo] },
      ],
    })
  )
  .flat();

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
      ],
    })
  )
  .flat();

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
    ],
  })
);

const dayProducts = leagueValues
  .map((league) =>
    createProduct({
      name: "Day",
      postfix: `- ${league.fields.name}`,
      postfixSlug: `-${league.fields.slug}`,
      price: "12.500",
      attributes: [
        { attribute: ticketTypeAttribute, values: [dayAttribute] },
        { attribute: leaguesAttribute, values: [league] },
        { attribute: streamTypeAttribute, values: [streamTypeGame] },
      ],
    })
  )
  .flat();

const monthProducts = leagueValues
  .map((league) => {
    const products = teamValues.map((team) =>
      createProduct({
        name: "Month",
        postfix: `- ${league.fields.name} - ${team.fields.name}`,
        postfixSlug: `-${league.fields.slug}-${team.fields.slug}`,
        price: "49.000",
        attributes: [
          { attribute: ticketTypeAttribute, values: [monthAttribute] },
          { attribute: leaguesAttribute, values: [league] },
          { attribute: teamsAttribute, values: [team] },
          { attribute: streamTypeAttribute, values: [streamTypeGame] },
        ],
      })
    );

    products.push(
      createProduct({
        name: "Month",
        price: "89.000",
        postfix: `- ${league.fields.name}`,
        postfixSlug: `-${league.fields.slug}`,
        attributes: [
          { attribute: ticketTypeAttribute, values: [monthAttribute] },
          { attribute: leaguesAttribute, values: [league] },
          { attribute: teamsAttribute, values: [allTeamValue] },
          { attribute: streamTypeAttribute, values: [streamTypeGame] },
        ],
      })
    );

    return products;
  })
  .flat()
  .flat();

const result = [
  ticketsCategory,
  ticketProductType,
  ticketTypeAttribute,
  streamTypeAttribute,
  leaguesAttribute,
  teamsAttribute,
  allTeamValue,
  ...attributeLinks,
  ...streamTypeValues,
  ...ticketTypeValues,
  ...teamValues,
  ...leagueValues,
  ...singleGameProducts,
  ...singleVideoProducts,
  ...seasonProducts,
  ...dayProducts,
  ...monthProducts,
];

fs.writeFile("./result.json", JSON.stringify(result), (err) => {
  if (err) {
    console.log(err);
  }
});

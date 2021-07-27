// @ts-ignore
const fs = require("fs");

import {
  createAttribute,
  createAttributeProductLinks,
  createAttributeValue,
  createProduct,
} from "./factories";
import { ticketProductType, ticketsCategory } from "./static-objects";

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

const attributeLinks = [ticketTypeAttribute, leaguesAttribute, teamsAttribute]
  .map((attribute) => createAttributeProductLinks(attribute))
  .flat();

const ticketTypeValues = [
  { name: "Single", slug: "single" },
  { name: "Season", slug: "season" },
  { name: "Month", slug: "month" },
  { name: "Day", slug: "day" },
].map((config) => createAttributeValue(ticketTypeAttribute, config));

const [singleAttribute, seasonAttribute, monthAttribute, dayAttribute] =
  ticketTypeValues;

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
  leaguesAttribute,
  teamsAttribute,
  allTeamValue,
  ...attributeLinks,
  ...ticketTypeValues,
  ...teamValues,
  ...leagueValues,
  ...singleProducts,
  ...seasonProducts,
  ...dayProducts,
  ...monthProducts,
];

fs.writeFile("./result.json", JSON.stringify(result), (err) => {
  if (err) {
    console.log(err);
  }
});

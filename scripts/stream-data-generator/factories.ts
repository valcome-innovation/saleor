import { AttributeConfig, AttributeValueConfig, Entity, ProductConfig } from './types';
import { ticketProductType, ticketsCategory } from './static-objects';

let attributePk = 0;
let attributeValuePk = 0;
let attributeProductPk = 0;
let productPk = 0;
let assignedAttributePk = 0;

export function createAttribute(config: AttributeConfig) {
  attributePk++;

  return {
    "model": "attribute.attribute",
    "pk": attributePk,
    "fields": {
      "private_metadata": {},
      "metadata": {},
      "slug": config.slug,
      "name": config.name,
      "type": "product-type",
      "input_type": config.input_type,
      "value_required": config.isRequired,
      "is_variant_only": false,
      "visible_in_storefront": true,
      "filterable_in_storefront": true,
      "filterable_in_dashboard": true,
      "storefront_search_position": 0,
      "available_in_grid": true
    }
  };
}

export function createAttributeValue(attribute: Entity, config: AttributeValueConfig) {
  attributeValuePk++;

  return {
    "model": "attribute.attributevalue",
    "pk": attributeValuePk,
    "fields": {
      "sort_order": attributeValuePk,
      "name": config.name,
      "slug": config.slug,
      "value": "",
      "attribute": attribute.pk
    }
  }
}

export function createAttributeProductLinks(attribute: Entity) {
  attributeProductPk++;

  return [
    {
      "model": "attribute.attributeproduct",
      "pk": attributeProductPk,
      "fields": {
        "sort_order": attributeProductPk,
        "attribute": attribute.pk,
        "product_type": ticketProductType.pk
      }
    },
    {
      "model": "attribute.attributevariant",
      "pk": attributeProductPk,
      "fields": {
        "sort_order": attributeProductPk,
        "attribute": attribute.pk,
        "product_type": ticketProductType.pk
      }
    }
  ];
}

export function createProduct(config: ProductConfig) {
  productPk++;

  return [
    {
      "model": "product.product",
      "pk": productPk,
      "fields": {
        "private_metadata": {},
        "metadata": {
          "vatlayer.code": "standard",
          "vatlayer.description": "standard"
        },
        "description_plaintext": `${config.name} Ticket`,
        "seo_title": "",
        "seo_description": `${config.name} Ticket ${config.postfix}`.trim(),
        "description": {
          "blocks": [{
            "data": {
              "text": `${config.name} Ticket`
            },
            "type": "paragraph"
          }]
        },
        "product_type": ticketProductType.pk,
        "name": `${config.name} Ticket ${config.postfix}`.trim(),
        "slug": `${config.name}-ticket${config.postfixSlug}`.replace(' ', '').toLowerCase(),
        "category": ticketsCategory.pk,
        "updated_at": "2020-04-17T14:22:48.130Z",
        "charge_taxes": true,
        "weight": "0.0:kg"
      }
    },
    {
      "model": "product.productvariant",
      "pk": productPk,
      "fields": {
        "private_metadata": {},
        "metadata": {},
        "sku": (productPk + 100).toString(),
        "name": config.name,
        "product": productPk,
        "track_inventory": false,
        "weight": "1.0:kg",
        "default": true
      }
    },
    {
      "model": "product.productchannellisting",
      "pk": productPk,
      "fields": {
        "publication_date": "2020-01-01",
        "is_published": true,
        "product": productPk,
        "channel": "EUR",
        "visible_in_listings": true,
        "available_for_purchase": "2020-08-31",
        "discounted_price_amount": config.price,
        "currency": "EUR"
      }
    },
    {
      "model": "product.productvariantchannellisting",
      "pk": productPk,
      "fields": {
        "variant": productPk,
        "channel": "EUR",
        "currency": "EUR",
        "price_amount": config.price,
        "cost_price_amount": config.price
      }
    },
    ...config.attributes.map(value => {
      assignedAttributePk++;

      return [{
          "model": "attribute.assignedproductattribute",
          "pk": assignedAttributePk,
          "fields": {
            "product": productPk,
            "assignment": value.attribute.pk,
            "values": value.values.map(v => v.pk)
          }
        }, {
          "model": "attribute.assignedvariantattribute",
          "pk": assignedAttributePk,
          "fields": {
            "variant": productPk,
            "assignment": value.attribute.pk,
            "values": value.values.map(v => v.pk)
          }
        }];
      }
    ).flat()
  ]
}

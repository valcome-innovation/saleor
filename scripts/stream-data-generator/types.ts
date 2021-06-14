export interface Entity {
  pk: number;
}

export type AttributeConfig = {
  slug: string;
  name: string;
  input_type: 'dropdown' | 'multiselect' | 'file' | 'text' | 'numeric' | 'references';
  isRequired: boolean;
}

export type AttributeValueConfig = {
  name: string;
  slug: string;
}

export type ProductConfig = {
  name: string,
  price: string;
  postfix: string,
  postfixSlug: string,
  attributes: {
    attribute: Entity,
    values: Entity[]
  }[]
}

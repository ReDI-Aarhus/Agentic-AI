---
name: meal-planner
description: Plan meals for a week with a unified shopping list, optimizing for ingredient reuse and weeknight prep time
---

# Meal Planner

When the user asks for meal planning, follow this approach.

## 1. Gather constraints

You need enough information to build a realistic plan. Ask only what's
missing:

- Number of people
- Days to cover (5 weeknights, full 7, dinners only, all meals)
- Typical weeknight cooking time
- Dietary restrictions or allergies
- Budget sensitivity (rough - cheap / mid / no limit)
- Any "no thanks" foods or cuisines

Default to dinner-only for 4 weeknights + a flex night if they didn't
specify.

## 2. Planning principles

- **Reuse ingredients** across 2-3 meals to minimize waste. Example: roast a
  big tray of chicken Monday → use leftovers in tacos Wednesday.
- **One slow-cook day at most.** Assume weeknights are 30 min max unless
  they said otherwise. Put longer recipes on weekends.
- **Vary protein and cuisine** so the week doesn't get monotonous.
- **Include one easy night** - leftovers, a quick pasta, or a "fridge
  cleanup" stir fry.
- **Anchor around what's in season** if relevant.

## 3. Output format

Present as three sections:

**Week plan**
- Mon: dish name (time)
- Tue: dish name (time)
- ...

**Shopping list** - grouped by store section (Produce / Protein / Dairy /
Pantry / Frozen). Combine quantities across recipes so they buy one number
of onions, not three.

**Prep-ahead tips** - 2-4 things they can do on Sunday (or whatever day
they shop) to make weeknights faster. Examples: pre-chop aromatics, marinate
the protein, cook a grain in bulk.

## 4. Offer to drill in

After the plan, mention you can pull up full recipes for any of the dishes
- that triggers the recipe-finder skill. Don't dump all the recipes
unprompted.

import { useCallback, useEffect, useMemo, useRef } from "react";
import { useForm } from "react-hook-form";
import type {
  DefaultValues,
  FieldValues,
  Resolver,
  UseFormReturn,
} from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import z, { type ZodObject, type ZodRawShape, type ZodType } from "zod";

/**
 * Custom hook for integrating Zod schemas with React Hook Form.
 *
 * This hook handles the complexity of normalizing optional/nullable fields
 * to work seamlessly with HTML form inputs (which use empty strings for
 * blank values) while maintaining type safety with Zod schemas.
 *
 * Key features:
 * - Automatic normalization of null/undefined to empty strings or default values
 * - Denormalization back to null/undefined when submitting
 * - Support for custom mappers for complex field transformations
 * - Field exclusion support for computed or server-only fields
 */

type Nil = null | undefined;

/**
 * Type utility to check if two types are exactly the same.
 *
 * This is useful for distinguishing between types that are structurally compatible
 * (i.e., assignable to each other) and types that are strictly identical.
 *
 * Why do we use tuple wrapping here?
 * - In TypeScript, conditional types are "distributive" over unions by default.
 *   That is, if you write `A extends B ? ... : ...` and `A` is a union,
 *   the check is performed for each member of the union separately.
 * - By wrapping the types in single-element tuples (`[A]` and `[B]`), we prevent
 *   this distributive behavior, ensuring that the comparison is made on the entire
 *   type, not its individual union members.
 *
 * Example:
 *   type T1 = IsExactly<string | number, string | number>; // true
 *   type T2 = IsExactly<string, string | number>; // false
 *   type T3 = IsExactly<undefined, undefined>; // true
 *
 * Wrong approach (not used here):
 *   // This version is distributive and can yield incorrect results for unions.
 *   type IsExactly_Distributive<A, B> = A extends B ? (B extends A ? true : false) : false;
 *
 *   // Corrected step-by-step example of the problem:
 *   // Let's check: IsExactly_Distributive<string | number, string | number>
 *   // 1. **Outer Distribution:** The check is distributed over A (`string | number`):
 *   //    - IsExactly_Distributive<string, string | number>
 *   //    - |
 *   //    - IsExactly_Distributive<number, string | number>
 *   // 2. **First Part:** IsExactly_Distributive<string, string | number>
 *   //    - string extends (string | number)? Yes, true.
 *   //    - Now check: (string | number) extends string ? true : false
 *   //      - **Inner Distribution:** This check is distributive over B (`string | number`):
 *   //        - string extends string => true
 *   //        - number extends string => false
 *   //      - Result: true | false => boolean
 *   //    - So, first part resolves to boolean.
 *   // 3. **Second Part:** IsExactly_Distributive<number, string | number>
 *   //    - number extends (string | number)? Yes, true.
 *   //    - Now check: (string | number) extends number ? true : false
 *   //      - **Inner Distribution:** Distributive over B:
 *   //        - string extends number => false
 *   //        - number extends number => true
 *   //      - Result: false | true => boolean
 *   //    - So, second part resolves to boolean.
 *   // 4. **Final Result:** boolean | boolean => boolean
 *   //
 *   // Thus, the distributive approach yields `boolean`, not `false`, for this case.
 *   // The tuple-wrapped version avoids this by comparing the whole type at once, not each union member.
 */
type IsExactly<A, B> = [A] extends [B]
  ? [B] extends [A]
    ? true
    : false
  : false;

/**
 * Type utilities to check if a field can be null, undefined, or both.
 * These help determine how to handle empty form values.
 */
type IsNullable<Base, Candidate> = IsExactly<Candidate, Base | null>;
type IsOptional<Base, Candidate> = IsExactly<Candidate, Base | undefined>;
type IsNullish<Base, Candidate> = IsExactly<Candidate, Base | Nil>;

/**
 * Determines if a field type can be nil (null/undefined).
 * Used to identify fields that need normalization.
 */
type MaybeNil<Base, Candidate> =
  IsNullish<Base, Candidate> extends true
    ? true
    : IsOptional<Base, Candidate> extends true
      ? true
      : IsNullable<Base, Candidate> extends true
        ? true
        : false;

/**
 * Normalizes an object type by replacing nullable/optional fields
 * with a base type (string or number) for form compatibility.
 * Example: { name: string | null } becomes { name: string }
 */
type Normalize<T extends object, Base> = {
  [K in keyof T]: MaybeNil<Base, T[K]> extends true // We check if the type of T[K] is null / undefined
    ? Base // If it is, we use the base type, which should not be null or undefined
    : T[K]; // If it is not, we use the type of T[K], which also should not be null or undefined
};

/**
 * Extracts only the fields that need default values for normalization.
 * These are fields that can be null/undefined and need to be converted
 * to empty strings or default numbers for form inputs.
 */
type NormalizationDefaults<T extends object, Base> = {
  [K in keyof T as MaybeNil<Base, T[K]> extends true ? K : never]: Base;
};

// interface test {
//   name: string | null,
//   birthday: string | undefined,
//   cake: string
// }

// type test2 = NormalizationDefaults<test, string>

/**
 * Combined type for all normalization defaults (strings and numbers).
 * The user must provide default values for these fields.
 */
type NormalizationDefaultValues<T extends object> = NormalizationDefaults<
  T,
  string
> &
  NormalizationDefaults<T, number>;

/**
 * Gets the normalized type of a specific field after all transformations.
 */
type NormalizedFieldValue<T extends object, K extends keyof T> = Normalize<
  Normalize<Pick<T, K>, string>,
  number
>[K];

/**
 * Custom mapper functions for denormalizing form values back to original types.
 * Useful for complex transformations like parsing dates or converting formats.
 *
 * Example:
 * mappers: {
 *   birthDate: (value: string) => value ? new Date(value) : null
 * }
 */
type DenormalizationMappers<T extends object> = {
  [K in keyof T]?: (value: NormalizedFieldValue<T, K>) => T[K];
};

type TupleKeys<Tuple extends readonly unknown[]> = Tuple[number];

const EMPTY_OMIT: readonly never[] = [];

/**
 * The final form values type after normalization and field exclusion.
 * This is what React Hook Form will work with.
 */
type FormValues<
  Obj extends ZodObject<ZodRawShape>,
  ExcludeKeys extends readonly (keyof z.infer<Obj>)[],
> = Normalize<
  Normalize<Omit<z.infer<Obj>, TupleKeys<ExcludeKeys>>, string>,
  number
>;

/**
 * Metadata about a field's original type before normalization.
 * Used to properly denormalize values when submitting the form.
 *
 * IMPORTANT: This tracks whether a field was originally nullable/optional
 * so we can convert empty strings back to null/undefined appropriately.
 */
interface FieldMeta {
  baseType: "string" | "number" | "other";
  wasNullable: boolean;
  wasOptional: boolean;
  requiresDefault: boolean;
}

type FieldMetaMap = Record<string, FieldMeta>;

type TypedUseFormReturn<T extends FieldValues> = UseFormReturn<T, undefined, T>;

type HandleSubmitFn<T extends FieldValues> = ReturnType<
  TypedUseFormReturn<T>["handleSubmit"]
>;

interface UseZodFormParams<
  Obj extends ZodObject<ZodRawShape>,
  ExcludeKeys extends readonly (keyof z.infer<Obj>)[] = [],
> {
  zodObject: Obj;
  initial: z.infer<Obj>;
  defaults: NormalizationDefaultValues<z.infer<Obj>>;
  mappers?: DenormalizationMappers<z.infer<Obj>>;
  omit?: ExcludeKeys;
  onUpdate: (input: z.infer<Obj>) => Promise<void> | void;
}

interface UseZodFormResult<
  Obj extends ZodObject<ZodRawShape>,
  ExcludeKeys extends readonly (keyof z.infer<Obj>)[],
> {
  form: TypedUseFormReturn<FormValues<Obj, ExcludeKeys>>;
  submit: HandleSubmitFn<FormValues<Obj, ExcludeKeys>>;
  schema: ZodObject<ZodRawShape>;
}

/**
 * Analyzes a Zod field to determine its base type and whether it needs normalization.
 * Unwraps ZodOptional and ZodNullable wrappers to find the underlying type.
 *
 * @param field - The Zod type to analyze
 * @returns Object containing:
 *   - normalized: The unwrapped base type (for strings/numbers) or original field
 *   - meta: Metadata about the field's original structure
 *   - replaced: Whether the field needs to be replaced in the schema
 *
 * IMPORTANT: This function is crucial for handling nullable/optional fields.
 * It strips away the optional/nullable wrappers so forms can work with
 * the base type (e.g., string instead of string | null).
 */
function buildFieldNormalization(field: ZodType): {
  normalized: ZodType;
  meta: FieldMeta;
  replaced: boolean;
} {
  let current = field;
  let wasOptional = false;
  let wasNullable = false;

  // Unwrap all Optional and Nullable wrappers
  while (current instanceof z.ZodOptional || current instanceof z.ZodNullable) {
    if (current instanceof z.ZodOptional) {
      wasOptional = true;
      current = current._def.innerType as ZodType;
      continue;
    }

    wasNullable = true;
    current = current._def.innerType as ZodType;
  }

  const baseType: FieldMeta["baseType"] =
    current instanceof z.ZodString
      ? "string"
      : current instanceof z.ZodNumber
        ? "number"
        : "other";

  // Non-string/number types don't need normalization
  if (baseType === "other") {
    return {
      normalized: field,
      meta: {
        baseType,
        wasNullable: false,
        wasOptional: false,
        requiresDefault: false,
      },
      replaced: false,
    };
  }

  // String/number types that were nullable/optional need normalization
  return {
    normalized: current,
    meta: {
      baseType,
      wasNullable,
      wasOptional,
      requiresDefault: wasNullable || wasOptional,
    },
    replaced: wasNullable || wasOptional,
  };
}

/**
 * Builds a normalized form schema from a Zod object schema.
 * Removes specified fields and normalizes nullable/optional fields.
 *
 * @param zodObject - The original Zod schema
 * @param omit - Array of field names to exclude from the form
 * @returns Object containing:
 *   - formSchema: The normalized schema for use with React Hook Form
 *   - meta: Metadata map for all fields
 *
 * WATCH OUT:
 * - Fields in the omit list won't be included in the form at all
 * - This modifies the schema to replace nullable/optional string/number
 *   fields with their base types (required string/number)
 */
function buildFormSchema<
  Obj extends ZodObject<ZodRawShape>,
  ExcludeKeys extends readonly (keyof z.infer<Obj>)[],
>(
  zodObject: Obj,
  omit: ExcludeKeys
): { formSchema: ZodObject<ZodRawShape>; meta: FieldMetaMap } {
  const omitMask = Object.fromEntries(omit.map((key) => [key, true])) as {
    [K in TupleKeys<ExcludeKeys>]: true;
  };

  const baseSchema = omit.length > 0 ? zodObject.omit(omitMask) : zodObject;
  const overrides: Record<string, ZodType> = {};
  const meta: FieldMetaMap = {};
  const shape = zodObject.shape;

  // Process each field in the schema
  for (const key of Object.keys(shape)) {
    if (key in omitMask) continue;

    const field = shape[key as keyof typeof shape] as ZodType;
    const {
      normalized,
      meta: fieldMeta,
      replaced,
    } = buildFieldNormalization(field);
    meta[key] = fieldMeta;

    // If the field was normalized, add it to overrides
    if (replaced) {
      overrides[key] = normalized;
    }
  }

  // Apply overrides to create the final form schema
  const formSchema = Object.keys(overrides).length
    ? baseSchema.extend(overrides as unknown as ZodRawShape)
    : baseSchema;

  return { formSchema, meta };
}

/**
 * Converts null/undefined values to their default form values.
 * This prepares data for use in HTML form inputs.
 *
 * @param data - The original data with potential null/undefined values
 * @param defaults - Default values for nullable/optional fields
 * @param meta - Field metadata map
 * @returns Normalized data with defaults applied
 *
 * IMPORTANT:
 * - Throws an error if a nullable/optional field doesn't have a default value
 * - Empty strings are used for nullable string fields
 * - Default numbers (like 0) are used for nullable number fields
 */
function normalizeValues<T extends Record<string, unknown>>(
  data: T,
  defaults: NormalizationDefaultValues<T>,
  meta: FieldMetaMap
): Normalize<Normalize<T, string>, number> {
  const normalized: Record<string, unknown> = {};
  const defaultRecord = defaults as unknown as Partial<
    Record<keyof T, unknown>
  >;

  for (const key of Object.keys(data) as Array<keyof T>) {
    const value = data[key];
    const fieldMeta = meta[String(key)];

    if (value === null || value === undefined) {
      if (fieldMeta?.requiresDefault) {
        if (!(key in defaultRecord)) {
          throw new Error(
            `useZodForm: missing normalization default for key "${String(key)}"`
          );
        }
        normalized[String(key)] = defaultRecord[key];
      } else {
        normalized[String(key)] = value;
      }
    } else {
      normalized[String(key)] = value;
    }
  }

  return normalized as Normalize<Normalize<T, string>, number>;
}

/**
 * Utility to omit specified keys from an object.
 * Used to exclude fields from form data.
 */
function omitKeysFromObject<
  T extends Record<string, unknown>,
  Keys extends readonly (keyof T)[],
>(data: T, omit: Keys) {
  if (!omit.length) {
    return { ...data } as Omit<T, TupleKeys<Keys>>;
  }

  const omitSet = new Set(omit.map((key) => String(key)));
  const result: Record<string, unknown> = {};

  for (const key of Object.keys(data)) {
    if (!omitSet.has(key)) {
      result[key] = data[key];
    }
  }

  return result as Omit<T, TupleKeys<Keys>>;
}

/**
 * Converts form values back to their original nullable/optional types.
 * This is the reverse of normalization, used when submitting the form.
 *
 * @param value - The current form value
 * @param meta - Field metadata indicating original type
 * @param defaultValue - The default value used for normalization
 * @param initialValue - The original value before normalization
 * @returns The denormalized value (potentially null/undefined)
 *
 * CRITICAL LOGIC:
 * - Empty strings → null (if field was nullable) or undefined (if optional)
 * - Default numbers → null/undefined based on original type
 * - Preserves the original null vs undefined distinction when possible
 *
 * WATCH OUT:
 * - The distinction between null and undefined is important for API compatibility
 * - Empty string handling is crucial for text inputs
 */
function applyDefaultDenormalization(
  value: unknown,
  meta: FieldMeta | undefined,
  defaultValue: unknown,
  initialValue: unknown
) {
  if (!meta) {
    return value;
  }

  // Handle string fields
  if (meta.baseType === "string" && typeof value === "string") {
    if (value === "" && (meta.wasNullable || meta.wasOptional)) {
      // Preserve original null vs undefined distinction
      if (meta.wasNullable && !meta.wasOptional) {
        return null;
      }
      if (!meta.wasNullable && meta.wasOptional) {
        return undefined;
      }
      // If both nullable and optional, use the initial value's type
      return initialValue === undefined ? undefined : null;
    }
    return value;
  }

  // Handle number fields
  if (meta.baseType === "number" && typeof value === "number") {
    if (meta.requiresDefault && defaultValue !== undefined) {
      if (typeof defaultValue === "number") {
        const defaultIsSentinel = Number.isNaN(defaultValue);
        const matchesDefault = defaultIsSentinel
          ? Number.isNaN(value)
          : Object.is(value, defaultValue);

        if (matchesDefault) {
          if (!defaultIsSentinel) {
            return value;
          }

          if (meta.wasNullable && !meta.wasOptional) {
            return null;
          }
          if (!meta.wasNullable && meta.wasOptional) {
            return undefined;
          }
          return initialValue === undefined ? undefined : null;
        }
      } else if (Object.is(value, defaultValue)) {
        if (meta.wasNullable && !meta.wasOptional) {
          return null;
        }
        if (!meta.wasNullable && meta.wasOptional) {
          return undefined;
        }
        return initialValue === undefined ? undefined : null;
      }
    }
    return value;
  }

  return value;
}

/**
 * Converts normalized form values back to their original Zod schema types.
 * Applies custom mappers if provided, otherwise uses default denormalization.
 *
 * @param values - The normalized form values
 * @param initial - The initial data before normalization
 * @param meta - Field metadata map
 * @param defaults - Default values used during normalization
 * @param mappers - Optional custom transformation functions
 * @returns The denormalized data matching the original Zod schema
 *
 * IMPORTANT:
 * - Custom mappers take precedence over default denormalization
 * - Preserves fields from initial data that weren't in the form
 * - Maintains null vs undefined distinction based on original data
 */
function denormalizeValues<
  Obj extends ZodObject<ZodRawShape>,
  ExcludeKeys extends readonly (keyof z.infer<Obj>)[],
>(
  values: FormValues<Obj, ExcludeKeys>,
  initial: z.infer<Obj>,
  meta: FieldMetaMap,
  defaults: NormalizationDefaultValues<z.infer<Obj>>,
  mappers?: DenormalizationMappers<z.infer<Obj>>
) {
  // Start with initial data to preserve omitted fields
  const result: Record<keyof z.infer<Obj>, unknown> = {
    ...(initial as Record<keyof z.infer<Obj>, unknown>),
  };
  const defaultRecord = defaults as unknown as Partial<
    Record<keyof z.infer<Obj>, unknown>
  >;

  for (const key of Object.keys(values) as Array<
    keyof FormValues<Obj, ExcludeKeys>
  >) {
    const originalKey = key as keyof z.infer<Obj>;
    const normalizedValue = values[key];
    const mapper = mappers?.[originalKey];

    // Use custom mapper if provided
    if (mapper) {
      result[originalKey] = mapper(normalizedValue as never);
      continue;
    }

    // Otherwise apply default denormalization
    const fieldMeta = meta[String(originalKey)];
    result[originalKey] = applyDefaultDenormalization(
      normalizedValue,
      fieldMeta,
      defaultRecord[originalKey],
      initial[originalKey]
    );
  }

  return result as z.infer<Obj>;
}

/**
 * Main hook for integrating Zod schemas with React Hook Form.
 * Handles normalization/denormalization of nullable/optional fields.
 *
 * @param params - Configuration object containing:
 *   - zodObject: The Zod schema defining the data structure
 *   - initial: Initial data values
 *   - defaults: Default values for nullable/optional fields (e.g., "" for strings)
 *   - mappers: Optional custom transformation functions
 *   - omit: Fields to exclude from the form
 *   - onUpdate: Callback when form is successfully submitted
 *
 * @returns Object containing:
 *   - form: React Hook Form instance
 *   - submit: Submit handler function
 *   - schema: The normalized Zod schema used by the form
 *
 * USAGE EXAMPLE:
 * ```tsx
 * const { form, submit } = useZodForm({
 *   zodObject: UserSchema,
 *   initial: userData,
 *   defaults: { name: "", age: 0 },
 *   omit: ["id", "createdAt"],
 *   onUpdate: async (data) => await saveUser(data)
 * });
 * ```
 *
 * KEY FEATURES:
 * 1. Automatic handling of null/undefined → empty string conversion
 * 2. Empty string → null/undefined conversion on submit
 * 3. Type-safe form with full Zod validation
 * 4. Support for excluding computed/readonly fields
 * 5. Custom transformation support via mappers
 *
 * WATCH OUT:
 * - You MUST provide defaults for ALL nullable/optional string/number fields
 * - The hook will throw an error if defaults are missing
 * - Form resets when initial data changes
 * - Uses refs to avoid stale closures in callbacks
 */
export function useZodForm<
  Obj extends ZodObject<ZodRawShape>,
  ExcludeKeys extends readonly (keyof z.infer<Obj>)[] = [],
>(
  params: UseZodFormParams<Obj, ExcludeKeys>
): UseZodFormResult<Obj, ExcludeKeys> {
  const { zodObject, initial, defaults, mappers, omit, onUpdate } = params;
  const omitList = omit ?? (EMPTY_OMIT as unknown as ExcludeKeys);

  // Build normalized schema and metadata
  const { formSchema, meta } = useMemo(
    () => buildFormSchema(zodObject, omitList),
    [zodObject, omitList]
  );

  // Use refs to avoid stale closures
  const defaultsRef = useRef(defaults);
  useEffect(() => {
    defaultsRef.current = defaults;
  }, [defaults]);

  const initialRef = useRef(initial);
  useEffect(() => {
    initialRef.current = initial;
  }, [initial]);

  const onUpdateRef = useRef(onUpdate);
  useEffect(() => {
    onUpdateRef.current = onUpdate;
  }, [onUpdate]);

  const mappersRef = useRef(mappers);
  useEffect(() => {
    mappersRef.current = mappers;
  }, [mappers]);

  // Normalize initial values for form
  const normalizedInitial = useMemo(
    () => normalizeValues(initial, defaults, meta),
    [initial, defaults, meta]
  );

  // Remove omitted fields from form values
  const formDefaultValues = useMemo(
    () =>
      omitKeysFromObject(normalizedInitial, omitList) as FormValues<
        Obj,
        ExcludeKeys
      >,
    [normalizedInitial, omitList]
  );

  // Create Zod resolver for React Hook Form
  const resolver = useMemo(
    () =>
      zodResolver(formSchema) as Resolver<
        FormValues<Obj, ExcludeKeys>,
        undefined,
        FormValues<Obj, ExcludeKeys>
      >,
    [formSchema]
  );

  // Initialize React Hook Form
  const form = useForm<
    FormValues<Obj, ExcludeKeys>,
    undefined,
    FormValues<Obj, ExcludeKeys>
  >({
    resolver,
    defaultValues: formDefaultValues as DefaultValues<
      FormValues<Obj, ExcludeKeys>
    >,
  });

  // Reset form when initial data changes
  useEffect(() => {
    form.reset(formDefaultValues);
  }, [form, formDefaultValues]);

  // Handle form submission
  const handleValid = useCallback(
    async (values: FormValues<Obj, ExcludeKeys>) => {
      // Denormalize values back to original types
      const denormalized = denormalizeValues(
        values,
        initialRef.current,
        meta,
        defaultsRef.current,
        mappersRef.current
      );
      // Validate with original schema
      const parsed = zodObject.parse(denormalized) as z.infer<Obj>;
      // Call update handler
      await onUpdateRef.current(parsed);
    },
    [meta, zodObject]
  );

  // Create submit handler
  const submit = useMemo(
    () => form.handleSubmit(handleValid),
    [form, handleValid]
  );

  return {
    form,
    submit,
    schema: formSchema,
  };
}

export type {
  FormValues,
  NormalizationDefaults,
  NormalizationDefaultValues,
  DenormalizationMappers,
};

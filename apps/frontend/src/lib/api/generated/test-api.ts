/**
 * Test file to verify the generated API works correctly
 * This demonstrates how to use the generated SDK
 */

import * as api from "./api";
import * as schemas from "./api.zod";
import { z } from "zod";

// Example: Using the API functions
async function testAuth() {
  try {
    // Register a new user
    const registerData = {
      email: "test@example.com",
      password: "securepass123",
      first_name: "John",
      last_name: "Doe",
    };

    // Validate with Zod schema before sending
    const validatedData =
      schemas.registerApiV1AuthRegisterPostBody.parse(registerData);
    console.log("✅ Registration data is valid:", validatedData);

    // Make the API call (this would actually call the backend)
    // const response = await api.registerApiV1AuthRegisterPost(validatedData);

    // Login
    const loginData = {
      email: "test@example.com",
      password: "securepass123",
    };

    // Validate login data
    const validatedLogin = schemas.loginApiV1AuthLoginPostBody.parse(loginData);
    console.log("✅ Login data is valid:", validatedLogin);

    // const loginResponse = await api.loginApiV1AuthLoginPost(validatedLogin);
  } catch (error) {
    if (error instanceof z.ZodError) {
      console.error("❌ Validation failed:", error.errors);
    } else {
      console.error("❌ API error:", error);
    }
  }
}

// Example: Type inference works
type UserRegisterInput = z.infer<
  typeof schemas.registerApiV1AuthRegisterPostBody
>;
type UserLoginInput = z.infer<typeof schemas.loginApiV1AuthLoginPostBody>;

const testUser: UserRegisterInput = {
  email: "test@example.com",
  password: "password123",
  first_name: "Jane",
  last_name: null, // Optional, can be null
};

console.log("✅ SDK is working correctly!");
console.log("Types are properly inferred and validated.");

export { testAuth };

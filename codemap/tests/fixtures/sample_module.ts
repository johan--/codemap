/**
 * Sample TypeScript module for testing CodeMap.
 */

// Type definitions
interface User {
    id: number;
    name: string;
    email?: string;
}

type Status = "pending" | "active" | "completed";

enum Role {
    Admin,
    User,
    Guest
}

// Simple function
function greet(name: string): string {
    return `Hello, ${name}!`;
}

// Async function
async function fetchUser(id: number): Promise<User> {
    const response = await fetch(`/api/users/${id}`);
    return response.json();
}

// Arrow function
const double = (x: number): number => x * 2;

// Async arrow function
const fetchData = async (url: string): Promise<Response> => {
    return await fetch(url);
};

// Class with methods
class UserService {
    private apiUrl: string;

    constructor(apiUrl: string) {
        this.apiUrl = apiUrl;
    }

    async getUser(id: number): Promise<User> {
        const response = await fetch(`${this.apiUrl}/users/${id}`);
        return response.json();
    }

    createUser(name: string, email: string): User {
        return { id: Date.now(), name, email };
    }

    deleteUser(id: number): void {
        console.log(`Deleting user ${id}`);
    }
}

// Generic class
class Container<T> {
    private value: T;

    constructor(value: T) {
        this.value = value;
    }

    getValue(): T {
        return this.value;
    }

    setValue(value: T): void {
        this.value = value;
    }
}

// Exported items
export { User, Status, Role, UserService, Container };
export default greet;

#include "Types.h"
#include "Embedding.h"
#include <iostream>
#include <iomanip>
#include <vector>
#include <cmath>
#include <cassert>

void printHeader(const std::string& title) {
    std::cout << "\n" << std::string(80, '=') << "\n";
    std::cout << "  " << title << "\n";
    std::cout << std::string(80, '=') << "\n";
}

void printSubHeader(const std::string& sub) {
    std::cout << "\n--- " << sub << " ---\n";
}

int main() {
    printHeader("FLIGHT BOOKING CAPABILITY EMBEDDING & COMPOSITION");

    // Define initial state and goals
    State state1;
    state1.set("User.authenticated", true);
    state1.set("Flight.selected", true);
    state1.set("Seats.available", true);
    state1.set("Booking.created", false);

    Goal goal1("Issue Ticket Goal");
    goal1.addCondition("Ticket.issued", true);

    std::cout << "Initial World: " << state1.toString() << "\n\n";

    // 1. CreateBooking
    Capability createBooking("CreateBooking", CapabilityType::API, "REST_HTTP");
    createBooking.addInput("flightId")
                 .addInput("userId")
                 .addOutput("bookingId")
                 .addPrecondition("Flight.selected", true)
                 .addPrecondition("Seats.available", true)
                 .addEffect("Booking.created", true)
                 .addResource("BOOKING_DB")
                 .setCost(10.0)
                 .setReliability(0.99)
                 .setAvailability(0.999);

    // 2. ProcessPayment
    Capability processPayment("ProcessPayment", CapabilityType::API, "PAYMENT_GW");
    processPayment.addInput("bookingId")
                  .addInput("paymentDetails")
                  .addOutput("paymentReceipt")
                  .addPrecondition("Booking.created", true)
                  .addEffect("Payment.processed", true)
                  .addResource("PAYMENT_GW")
                  .setCost(20.0)
                  .setReliability(0.98)
                  .setAvailability(0.995);

    // 3. IssueTicket
    Capability issueTicket("IssueTicket", CapabilityType::SERVICE, "TICKET_SERVICE");
    issueTicket.addInput("bookingId")
               .addInput("paymentReceipt")
               .addOutput("ticketId")
               .addPrecondition("Payment.processed", true)
               .addEffect("Ticket.issued", true)
               .addResource("TICKET_DB")
               .setCost(5.0)
               .setReliability(0.999)
               .setAvailability(0.999);

    std::cout << createBooking.toString() << "\n\n";
    std::cout << processPayment.toString() << "\n\n";
    std::cout << issueTicket.toString() << "\n\n";

    printSubHeader("Test 1: Compatibility (CreateBooking -> ProcessPayment)");
    CompatibilityReport rep1 = checkCompatibility(createBooking, processPayment);
    std::cout << rep1.toString();
    
    printSubHeader("Test 2: Composition (CreateBooking -> ProcessPayment)");
    Capability comp1 = composeCapabilities(createBooking, processPayment);
    std::cout << "Composite Capability:\n" << comp1.toString() << "\n\n";
    
    printSubHeader("Test 3: Extended Composition (Comp1 -> IssueTicket)");
    Capability comp2 = composeCapabilities(comp1, issueTicket);
    std::cout << "Final Composite Capability:\n" << comp2.toString() << "\n\n";

    return 0;
}

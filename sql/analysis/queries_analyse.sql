-- Idée de requêtes d'analyse pour valider votre modèle gold.

-- Les requêtes "métier" ne sont pas implémenté pour ne pas 
-- donner trop d'indices sur le data modèle attendu. Mais vous
-- êtes libre d'essayer d'implémenter ces requêtes pour valider
-- votre conception.

-- 1. Chiffre d'affaires par mois et par devise

SELECT
    DATE_TRUNC('month', booking_date) AS month,
    currency,
    ROUND(SUM(amount),2) AS total_revenue,
FROM fact_booking
GROUP BY
    DATE_TRUNC('month', booking_date),
    currency
ORDER BY month, currency;

-- 2. Top 10 des compagnies aériennes par chiffre d'affaires

SELECT
    df.airline,
    ROUND(SUM(fb.amount_eur),2) AS total_ca_eur,
FROM fact_booking AS fb
JOIN dim_flight AS df
    ON fb.flight_id = df.flight_id
GROUP BY df.airline
ORDER BY total_ca_eur DESC
LIMIT 10;

-- 3. Répartition des réservations par classe de cabine

SELECT
    seat_class,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    ) AS percentage
FROM fact_booking
GROUP BY seat_class
ORDER BY percentage DESC;

-- 4. Volume de réservations par jour de la semaine

SELECT
    DAYNAME(booking_date) AS day_of_week,
    DAYOFWEEK(booking_date) AS day_number,
    COUNT(*) AS total_bookings
FROM fact_booking
GROUP BY
    DAYNAME(booking_date),
    DAYOFWEEK(booking_date)
ORDER BY day_number;

-- 5. Top 10 des aéroports de départ générant le plus de réservations
-- (airport_id sur une réservation = origin_airport_id du vol réservé)

SELECT
    da.airport_name,
    COUNT(fb.booking_id) AS total_bookings
FROM fact_booking AS fb
JOIN dim_flight AS df
    ON fb.flight_id = df.flight_id
JOIN dim_airport AS da
    ON df.origin_airport_id = da.airport_id
GROUP BY
    da.airport_id,
    da.airport_name
ORDER BY total_bookings DESC
LIMIT 10;

-- 6. Évolution quotidienne du nombre de réservations sur septembre

SELECT
    booking_date,
    COUNT(*) AS total_bookings
FROM fact_booking
WHERE booking_date >= DATE '2025-09-01'
  AND booking_date < DATE '2025-10-01'
GROUP BY booking_date
ORDER BY booking_date;

-- 7. Chiffre d'affaires normalisé en EUR

SELECT
    DATE_TRUNC('year', booking_date) AS year,
    ROUND(SUM(amount_eur),2) AS ca_eur
FROM fact_booking
GROUP BY DATE_TRUNC('year', booking_date)
ORDER BY year;

-- 8. Durée moyenne de vol par compagnie


-- 9. Chiffre d'affaires par tranche d'âge de passager

SELECT
    CASE
        WHEN DATE_DIFF('year', dp.birth_date, CURRENT_DATE) < 18
            THEN 'Moins de 18 ans'
        WHEN DATE_DIFF('year', dp.birth_date, CURRENT_DATE) BETWEEN 18 AND 25
            THEN '18-25 ans'
        WHEN DATE_DIFF('year', dp.birth_date, CURRENT_DATE) BETWEEN 26 AND 35
            THEN '26-35 ans'
        WHEN DATE_DIFF('year', dp.birth_date, CURRENT_DATE) BETWEEN 36 AND 50
            THEN '36-50 ans'
        WHEN DATE_DIFF('year', dp.birth_date, CURRENT_DATE) BETWEEN 51 AND 65
            THEN '51-65 ans'
        ELSE 'Plus de 65 ans'
    END AS age_group,
    ROUND(SUM(fb.amount_eur),2) AS total_revenue_eur
FROM fact_booking AS fb
JOIN dim_passenger AS dp
    ON fb.passenger_id = dp.passenger_id
WHERE dp.birth_date IS NOT NULL
GROUP BY age_group
ORDER BY MIN(DATE_DIFF('year', dp.birth_date, CURRENT_DATE));
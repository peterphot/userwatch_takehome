create table race_results as
    select
        horses.name
        , horses.horse_id
        , horses.stable_name
        , races.place
        , races.gate
        , races.race_id
    from races
    join horses
        on horses.horse_id = races.horse_id
    where True
;
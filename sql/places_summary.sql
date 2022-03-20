create table place_summary as
with places as (
    select distinct
        place
    from races
), horses as (
    select distinct
        horse_id
    from races
), place_prep as (
    select
        place
         , horse_id
    from places
     join horses
          on True
)



select
    place_prep.horse_id
     , place_prep.place
     , count(races.place) as number_of_places
from place_prep
left join races
    on place_prep.place = races.place
       and place_prep.horse_id = races.horse_id
where True
group by 1, 2;
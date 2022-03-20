create table gate_summary as
with gates as (
    select distinct
        gate
    from races
), horses as (
    select distinct
        horse_id
    from races
), gate_prep as (
    select
        gate
        , horse_id
    from gates
    join horses
        on True
)



select
    gate_prep.horse_id
     , gate_prep.gate
     , count(races.gate) as number_of_starts
from gate_prep
left join races
       on gate_prep.gate = races.gate
        and gate_prep.horse_id = races.horse_id
where True
group by 1, 2;
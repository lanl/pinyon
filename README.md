# Pinyon

Pinyon is a tool for managing the process of generating data-driven models. Pinyon stores each step in the model-building process,
from loading data from a database to generating visualizations, in a database (MongoDB) and allows users to run or edit each step 
through a web interface. By housing each step in model building process in one location along with documentation, reproducing
or updating the models as more data is collect will be drastically simplified.

## Requirements

- MongoDB
- Python libraries listed in `requirements.txt`

## Copyright and license

Los Alamos National Security, LLC (LANS) owns the copyright to Pinyon, which it identifies internally as LA-CC 17-025. The license is BSD-ish with a "modifications must be indicated" clause. See LICENSE.md for the full text.
